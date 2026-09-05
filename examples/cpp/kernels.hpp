#pragma once
// Original teaching kernels. No performance superiority is claimed.
// See ../../references/sources.md: D01, D02, T04, A05, A19.
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <stdexcept>

#if defined(__x86_64__) && (defined(__GNUC__) || defined(__clang__))
#define PE_X86_GNU 1
#include <immintrin.h>
#else
#define PE_X86_GNU 0
#endif
#if defined(__aarch64__)
#include <arm_neon.h>
#endif

namespace pe {
inline constexpr std::size_t not_found = std::numeric_limits<std::size_t>::max();

// Zero-sized requests bypass the pool. Subtraction is guarded against underflow.
constexpr bool fits_within_2x(std::size_t capacity, std::size_t need) noexcept {
    return need != 0 && capacity >= need && capacity - need <= need;
}

// Contract for byte functions: p points to n readable bytes, or n==0.
inline std::size_t find_byte_scalar(const std::uint8_t* p, std::size_t n,
                                    std::uint8_t needle) noexcept {
    for (std::size_t i = 0; i < n; ++i) if (p[i] == needle) return i;
    return not_found;
}

#if PE_X86_GNU
__attribute__((target("sse2")))
inline std::size_t find_byte_sse2(const std::uint8_t* p, std::size_t n,
                                 std::uint8_t needle) noexcept {
    // Broadcast unsigned numeric value without an out-of-range unsigned->char cast.
    const __m128i word = _mm_set1_epi16(static_cast<short>(needle));
    const __m128i key = _mm_packus_epi16(word, word);
    std::size_t i = 0;
    while (n - i >= 16) {
        // loadu permits unaligned data; the loop proves 16 readable bytes.
        const auto v = _mm_loadu_si128(reinterpret_cast<const __m128i*>(p + i));
        const unsigned mask = static_cast<unsigned>(_mm_movemask_epi8(_mm_cmpeq_epi8(v, key)));
        if (mask != 0) return i + static_cast<unsigned>(__builtin_ctz(mask));
        i += 16;
    }
    for (; i < n; ++i) if (p[i] == needle) return i;
    return not_found;
}

__attribute__((target("avx2")))
inline std::size_t find_byte_avx2(const std::uint8_t* p, std::size_t n,
                                 std::uint8_t needle) noexcept {
    const __m256i word = _mm256_set1_epi16(static_cast<short>(needle));
    const __m256i key = _mm256_packus_epi16(word, word);
    std::size_t i = 0;
    while (n - i >= 32) {
        const auto v = _mm256_loadu_si256(reinterpret_cast<const __m256i*>(p + i));
        const unsigned mask = static_cast<unsigned>(_mm256_movemask_epi8(_mm256_cmpeq_epi8(v, key)));
        if (mask != 0) return i + static_cast<unsigned>(__builtin_ctz(mask));
        i += 32;
    }
    for (; i < n; ++i) if (p[i] == needle) return i;
    return not_found;
}
#endif

#if defined(__aarch64__)
inline std::size_t find_byte_neon(const std::uint8_t* p, std::size_t n,
                                 std::uint8_t needle) noexcept {
    const uint8x16_t key = vdupq_n_u8(needle);
    std::size_t i = 0;
    while (n - i >= 16) {
        const uint8x16_t eq = vceqq_u8(vld1q_u8(p + i), key);
        // Portable AArch64 recipe: reject a block with NEON; resolve first match scalarly.
        if (vmaxvq_u8(eq) != 0) {
            for (std::size_t j = 0; j < 16; ++j) if (p[i + j] == needle) return i + j;
        }
        i += 16;
    }
    for (; i < n; ++i) if (p[i] == needle) return i;
    return not_found;
}
#endif

using FindByte = std::size_t (*)(const std::uint8_t*, std::size_t, std::uint8_t);
inline FindByte select_find_byte() noexcept {
#if PE_X86_GNU
    __builtin_cpu_init();
    if (__builtin_cpu_supports("avx2")) return find_byte_avx2;
    return find_byte_sse2; // SSE2 is the x86-64 baseline for this example.
#elif defined(__aarch64__)
    return find_byte_neon; // This example assumes a normal NEON-enabled AArch64 target.
#else
    return find_byte_scalar;
#endif
}
inline std::size_t find_byte(const std::uint8_t* p, std::size_t n,
                             std::uint8_t needle) noexcept {
    static const FindByte kernel = select_find_byte();
    return kernel(p, n, needle);
}

// Inclusive prefix sum modulo 2^32, in place.
inline void prefix_sum_scalar(std::uint32_t* p, std::size_t n) noexcept {
    std::uint32_t carry = 0;
    for (std::size_t i = 0; i < n; ++i) { carry += p[i]; p[i] = carry; }
}
#if PE_X86_GNU
__attribute__((target("sse2")))
inline void prefix_sum_sse2(std::uint32_t* p, std::size_t n) noexcept {
    __m128i carry_vector = _mm_setzero_si128();
    std::size_t i = 0;
    while (n - i >= 4) {
        auto v = _mm_loadu_si128(reinterpret_cast<const __m128i*>(p + i));
        v = _mm_add_epi32(v, _mm_slli_si128(v, 4));
        v = _mm_add_epi32(v, _mm_slli_si128(v, 8));
        v = _mm_add_epi32(v, carry_vector);
        _mm_storeu_si128(reinterpret_cast<__m128i*>(p + i), v);
        carry_vector = _mm_shuffle_epi32(v, _MM_SHUFFLE(3, 3, 3, 3));
        i += 4;
    }
    std::uint32_t carry = i == 0 ? 0 : p[i - 1];
    for (; i < n; ++i) { carry += p[i]; p[i] = carry; }
}
#endif

// Independent scalar tables reduce same-counter dependencies; not a SIMD scatter.
inline std::array<std::uint64_t, 256> histogram4(const std::uint8_t* p, std::size_t n) {
    static_assert(sizeof(std::size_t) <= sizeof(std::uint64_t), "count range contract");
    std::array<std::array<std::uint64_t, 256>, 4> local{};
    std::size_t i = 0;
    while (n - i >= 4) {
        ++local[0][p[i]]; ++local[1][p[i + 1]];
        ++local[2][p[i + 2]]; ++local[3][p[i + 3]];
        i += 4;
    }
    for (; i < n; ++i) ++local[0][p[i]];
    std::array<std::uint64_t, 256> out{};
    for (std::size_t k = 0; k < out.size(); ++k)
        out[k] = local[0][k] + local[1][k] + local[2][k] + local[3][k];
    return out;
}

inline std::size_t argmin_first(const std::uint32_t* p, std::size_t n) noexcept {
    if (n == 0) return not_found;
    std::size_t best = 0;
    for (std::size_t i = 1; i < n; ++i) if (p[i] < p[best]) best = i;
    return best;
}

// Domain: positive u32. Scalar teaching model, not a production vector-math routine.
// Only the real-arithmetic truncation bound is derived in computations.md.
inline double log2_u32_teaching(std::uint32_t value) {
    if (value == 0) throw std::domain_error("log2_u32_teaching requires positive input");
    unsigned k = 0;
    for (std::uint32_t q = value; q > 1; q >>= 1) ++k;
    const double m = std::ldexp(static_cast<double>(value), -static_cast<int>(k));
    const double z = (m - 1.0) / (m + 1.0);
    const double z2 = z * z;
    const double poly = 1.0 + z2 * (1.0 / 3.0 + z2 * (1.0 / 5.0
                      + z2 * (1.0 / 7.0 + z2 / 9.0)));
    constexpr double two_over_ln2 = 2.8853900817779268147;
    return static_cast<double>(k) + two_over_ln2 * z * poly;
}
} // namespace pe
