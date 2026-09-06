#include "kernels.hpp"
#include <algorithm>
#include <iostream>
#include <random>
#include <string>
#include <utility>
#include <vector>
#if defined(__unix__) || defined(__APPLE__)
#include <sys/mman.h>
#include <unistd.h>
#endif

namespace {
std::uint64_t checks = 0;
void check(bool result, const char* message) {
    ++checks;
    if (!result) throw std::runtime_error(message);
}
using NamedFinder = std::pair<const char*, pe::FindByte>;
std::vector<NamedFinder> finders() {
    std::vector<NamedFinder> out{{"scalar", pe::find_byte_scalar}, {"dispatch", pe::find_byte}};
#if PE_X86_GNU
    out.emplace_back("sse2", pe::find_byte_sse2);
    __builtin_cpu_init();
    if (__builtin_cpu_supports("avx2")) out.emplace_back("avx2", pe::find_byte_avx2);
#endif
#if defined(__aarch64__)
    out.emplace_back("neon", pe::find_byte_neon);
#endif
    return out;
}
void test_find(const std::vector<NamedFinder>& funcs) {
    std::mt19937 rng(42);
    for (const auto& f : funcs) check(f.second(nullptr, 0, 0) == pe::not_found, "empty null search");
    for (std::size_t n = 0; n <= 513; ++n) {
        for (std::size_t offset = 0; offset < 64; ++offset) {
            std::vector<std::uint8_t> storage(n + offset + 1);
            for (auto& v : storage) v = static_cast<std::uint8_t>(rng());
            const auto* p = storage.data() + offset;
            for (unsigned key : {0u, 1u, 127u, 128u, 254u, 255u}) {
                const auto needle = static_cast<std::uint8_t>(key);
                const auto reference = pe::find_byte_scalar(p, n, needle);
                for (const auto& f : funcs) check(f.second(p, n, needle) == reference, "random search");
            }
        }
    }
    for (std::size_t n : {15u, 16u, 17u, 31u, 32u, 33u, 63u, 64u, 65u, 129u}) {
        std::vector<std::uint8_t> values(n, 0);
        for (std::size_t i = 0; i < n; ++i) {
            values[i] = 255;
            for (const auto& f : funcs) check(f.second(values.data(), n, 255) == i, "every match lane");
            values[i] = 0;
        }
        std::fill(values.begin(), values.end(), 255);
        for (const auto& f : funcs) check(f.second(values.data(), n, 255) == 0, "first duplicate");
    }
}
void test_guard_page(const std::vector<NamedFinder>& funcs) {
#if defined(__unix__) || defined(__APPLE__)
    const long raw_page = sysconf(_SC_PAGESIZE);
    check(raw_page > 0, "page size");
    const auto page = static_cast<std::size_t>(raw_page);
    void* mapping = mmap(nullptr, page * 2, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    check(mapping != MAP_FAILED, "mmap guard test");
    auto* bytes = static_cast<std::uint8_t*>(mapping);
    if (mprotect(bytes + page, page, PROT_NONE) != 0) {
        munmap(mapping, page * 2);
        throw std::runtime_error("mprotect guard test");
    }
    for (std::size_t i = 0; i < page; ++i) bytes[i] = static_cast<std::uint8_t>(i * 37);
    for (std::size_t n = 0; n <= std::min<std::size_t>(page, 257); ++n) {
        const auto* p = bytes + page - n;
        for (unsigned key : {0u, 127u, 255u}) {
            const auto k = static_cast<std::uint8_t>(key);
            const auto expected = pe::find_byte_scalar(p, n, k);
            for (const auto& f : funcs) check(f.second(p, n, k) == expected, "guard boundary search");
        }
    }
    check(munmap(mapping, page * 2) == 0, "munmap guard test");
    std::cout << "guard_page=PASS\n";
#else
    std::cout << "guard_page=SKIP (no POSIX mapping API)\n";
#endif
}
void test_pool() {
    for (std::size_t need = 0; need < 1000; ++need)
        for (std::size_t cap = 0; cap < 2000; ++cap)
            check(pe::fits_within_2x(cap, need) == (need != 0 && cap >= need && cap <= 2 * need), "pool fit");
    constexpr auto m = std::numeric_limits<std::size_t>::max();
    check(pe::fits_within_2x(m, m), "pool max equal");
    check(pe::fits_within_2x(m, m / 2 + 1), "pool max fit");
    check(!pe::fits_within_2x(m, m / 2), "pool max oversized");
    check(!pe::fits_within_2x(m, 0), "pool zero bypass");
}
void test_histogram_prefix_argmin() {
    std::mt19937 rng(7);
    for (std::size_t n = 0; n < 2050; ++n) {
        std::vector<std::uint8_t> bytes(n);
        std::array<std::uint64_t, 256> expected{};
        for (auto& b : bytes) { b = static_cast<std::uint8_t>(rng()); ++expected[b]; }
        check(pe::histogram4(bytes.data(), n) == expected, "histogram random");
        std::fill(bytes.begin(), bytes.end(), 255);
        expected.fill(0); expected[255] = n;
        check(pe::histogram4(bytes.data(), n) == expected, "histogram collisions");
        std::vector<std::uint32_t> values(n);
        for (auto& v : values) v = rng();
        const auto min_it = std::min_element(values.begin(), values.end());
        const auto min_index = n == 0 ? pe::not_found : static_cast<std::size_t>(min_it - values.begin());
        check(pe::argmin_first(values.data(), n) == min_index, "first argmin");
        auto reference = values;
        pe::prefix_sum_scalar(reference.data(), n);
#if PE_X86_GNU
        auto actual = values;
        pe::prefix_sum_sse2(actual.data(), n);
        check(actual == reference, "SSE2 modular prefix sum");
#endif
    }
    const std::uint32_t maxes[]{UINT32_MAX, UINT32_MAX, UINT32_MAX};
    check(pe::argmin_first(maxes, 3) == 0, "argmin sentinel collision");
    const std::uint32_t ties[]{8, 3, 3, 9};
    check(pe::argmin_first(ties, 4) == 1, "argmin first tie");
    const std::uint32_t overflow[]{UINT32_MAX, 1, UINT32_MAX, 5, 9};
    auto expected = std::vector<std::uint32_t>(overflow, overflow + 5);
    pe::prefix_sum_scalar(expected.data(), expected.size());
    check(expected == std::vector<std::uint32_t>({UINT32_MAX, 0, UINT32_MAX, 4, 13}), "modular prefix oracle");
#if PE_X86_GNU
    auto actual = std::vector<std::uint32_t>(overflow, overflow + 5);
    pe::prefix_sum_sse2(actual.data(), actual.size());
    check(actual == expected, "explicit SIMD prefix overflow");
#endif
}
void test_logarithm() {
    const double z = 1.0 / 3.0;
    const double truncation_bound = 2.0 / std::log(2.0) * std::pow(z, 11) / (11.0 * (1.0 - z * z));
    double max_error = 0;
    auto test = [&](std::uint32_t x) {
        const double got = pe::log2_u32_teaching(x);
        const double error = std::abs(got - std::log2(static_cast<double>(x)));
        max_error = std::max(max_error, error);
        // Empirical check only: the added epsilon is not a certified rounding bound.
        check(error <= truncation_bound + 1e-12, "sampled logarithm error");
    };
    bool rejected_zero = false;
    try { (void)pe::log2_u32_teaching(0); } catch (const std::domain_error&) { rejected_zero = true; }
    check(rejected_zero, "log rejects zero");
    for (std::uint32_t x = 1; x <= 65536; ++x) test(x);
    std::mt19937 rng(19);
    for (unsigned i = 0; i < 250000; ++i) test(rng() | 1u);
    for (unsigned k = 0; k < 32; ++k) {
        const auto x = std::uint32_t{1} << k;
        check(pe::log2_u32_teaching(x) == k, "log power of two");
        test(x); if (x > 1) test(x - 1); test(x + 1);
    }
    test(UINT32_MAX);
    std::cout << "log_sample_max_abs_error=" << max_error << '\n';
    std::cout << "log_real_arithmetic_truncation_bound=" << truncation_bound << '\n';
}
} // namespace
int main() {
    try {
        const auto funcs = finders();
        std::cout << "executed_byte_kernels=";
        for (const auto& f : funcs) std::cout << f.first << ' ';
        std::cout << '\n';
        test_find(funcs); test_guard_page(funcs); test_pool();
        test_histogram_prefix_argmin(); test_logarithm();
        std::cout << "checks=" << checks << "\nresult=PASS\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "FAIL: " << e.what() << '\n';
        return 1;
    }
}
