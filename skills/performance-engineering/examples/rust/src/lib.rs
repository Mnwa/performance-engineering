//! Original teaching kernels, not claims of being faster than standard libraries.
//! See ../../../references/{allocations,computations,simd,rust}.md.
//! Native compilation/execution coverage is recorded separately in validation/.
#![deny(unsafe_op_in_unsafe_fn)]

use std::collections::TryReserveError;
use std::num::NonZeroU32;

/// Overflow-safe policy: need <= capacity <= 2*need; zero-sized requests bypass.
pub fn fits_within_2x(capacity: usize, need: usize) -> bool {
    need != 0 && capacity >= need && capacity - need <= need
}

/// Reuse caller-owned capacity. On reserve failure, previous output is intact.
/// Arithmetic is explicitly modulo 2^32, independent of build overflow settings.
pub fn map_reusing(input: &[u32], output: &mut Vec<u32>) -> Result<(), TryReserveError> {
    let additional = input.len().saturating_sub(output.len());
    output.try_reserve(additional)?;
    output.clear();
    for &x in input {
        output.push(x.wrapping_mul(3).wrapping_add(1));
    }
    Ok(())
}

pub fn affine(input: &[u32], output: &mut [u32]) {
    assert_eq!(input.len(), output.len());
    for (dst, &src) in output.iter_mut().zip(input) {
        *dst = src.wrapping_mul(3).wrapping_add(1);
    }
}

pub fn argmin_first(input: &[u32]) -> Option<usize> {
    let mut value = *input.first()?;
    let mut index = 0;
    for (i, &candidate) in input.iter().enumerate().skip(1) {
        if candidate < value { value = candidate; index = i; }
    }
    Some(index)
}

pub fn prefix_sum_wrapping(input: &mut [u32]) {
    let mut carry = 0u32;
    for x in input { carry = carry.wrapping_add(*x); *x = carry; }
}

/// Four independent scalar tables, NOT a conflicting SIMD scatter.
/// Table initialization and merging are intentionally part of this operation.
pub fn histogram4(input: &[u8]) -> [u64; 256] {
    let mut local = [[0u64; 256]; 4];
    let mut blocks = input.chunks_exact(4);
    for block in &mut blocks {
        local[0][usize::from(block[0])] += 1;
        local[1][usize::from(block[1])] += 1;
        local[2][usize::from(block[2])] += 1;
        local[3][usize::from(block[3])] += 1;
    }
    for &x in blocks.remainder() { local[0][usize::from(x)] += 1; }
    let mut output = [0; 256];
    for (i, x) in output.iter_mut().enumerate() {
        *x = local[0][i] + local[1][i] + local[2][i] + local[3][i];
    }
    output
}

/// Positive-u32 scalar teaching model. NOT a certified libm replacement.
/// The reference derives a real-arithmetic truncation bound, not a complete
/// compiled floating-point error bound. NonZeroU32 excludes log2(0) explicitly.
pub fn log2_u32_teaching(value: NonZeroU32) -> f64 {
    let value = value.get();
    let k = 31 - value.leading_zeros();
    let m = f64::from(value) / f64::from(1u32 << k);
    let z = (m - 1.0) / (m + 1.0);
    let z2 = z * z;
    let poly = 1.0 + z2 * (1.0 / 3.0 + z2 * (1.0 / 5.0
        + z2 * (1.0 / 7.0 + z2 / 9.0)));
    f64::from(k) + (2.0 * std::f64::consts::LOG2_E) * z * poly
}

pub fn find_byte_scalar(input: &[u8], needle: u8) -> Option<usize> {
    input.iter().position(|&x| x == needle)
}

/// Safe boundary. Feature dispatch occurs outside vector loops.
pub fn find_byte(input: &[u8], needle: u8) -> Option<usize> {
    #[cfg(target_arch = "x86_64")]
    {
        if std::is_x86_feature_detected!("avx2") {
            // SAFETY: runtime detector establishes AVX2; slice validity is retained.
            return unsafe { find_byte_avx2(input, needle) };
        }
        // SAFETY: SSE2 is baseline on x86-64; slice validity is retained.
        return unsafe { find_byte_sse2(input, needle) };
    }
    #[cfg(target_arch = "aarch64")]
    {
        if std::arch::is_aarch64_feature_detected!("neon") {
            // SAFETY: runtime detector establishes NEON; slice validity is retained.
            return unsafe { find_byte_neon(input, needle) };
        }
    }
    #[cfg(not(target_arch = "x86_64"))]
    find_byte_scalar(input, needle)
}

#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "sse2")]
unsafe fn find_byte_sse2(input: &[u8], needle: u8) -> Option<usize> {
    use std::arch::x86_64::*;
    // SAFETY: caller establishes SSE2. Each load is unaligned-capable and has
    // 16 initialized bytes within input. No stores or aliasing changes occur.
    unsafe {
        let key = _mm_set1_epi8(needle as i8); // Rust cast preserves the low byte.
        let mut i = 0;
        while input.len() - i >= 16 {
            let v = _mm_loadu_si128(input.as_ptr().add(i).cast::<__m128i>());
            let mask = _mm_movemask_epi8(_mm_cmpeq_epi8(v, key)) as u32;
            if mask != 0 { return Some(i + mask.trailing_zeros() as usize); }
            i += 16;
        }
        find_byte_scalar(&input[i..], needle).map(|j| i + j)
    }
}

#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2")]
unsafe fn find_byte_avx2(input: &[u8], needle: u8) -> Option<usize> {
    use std::arch::x86_64::*;
    // SAFETY: caller establishes AVX2. Every load reads a complete 32-byte block
    // in the input allocation; the incomplete tail uses safe scalar iteration.
    unsafe {
        let key = _mm256_set1_epi8(needle as i8);
        let mut i = 0;
        while input.len() - i >= 32 {
            let v = _mm256_loadu_si256(input.as_ptr().add(i).cast::<__m256i>());
            let mask = _mm256_movemask_epi8(_mm256_cmpeq_epi8(v, key)) as u32;
            if mask != 0 { return Some(i + mask.trailing_zeros() as usize); }
            i += 32;
        }
        find_byte_scalar(&input[i..], needle).map(|j| i + j)
    }
}

#[cfg(target_arch = "aarch64")]
#[target_feature(enable = "neon")]
unsafe fn find_byte_neon(input: &[u8], needle: u8) -> Option<usize> {
    use std::arch::aarch64::*;
    // SAFETY: caller establishes NEON. Each load reads 16 initialized in-bounds
    // bytes. A matching block is resolved scalarly to preserve the first match.
    unsafe {
        let key = vdupq_n_u8(needle);
        let mut i = 0;
        while input.len() - i >= 16 {
            let equal = vceqq_u8(vld1q_u8(input.as_ptr().add(i)), key);
            if vmaxvq_u8(equal) != 0 {
                return find_byte_scalar(&input[i..i + 16], needle).map(|j| i + j);
            }
            i += 16;
        }
        find_byte_scalar(&input[i..], needle).map(|j| i + j)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn pool_fit_exhaustive_small_and_overflow_boundaries() {
        for need in 0..512 {
            for cap in 0..1024 {
                assert_eq!(fits_within_2x(cap, need), need != 0 && cap >= need && cap <= 2 * need);
            }
        }
        let m = usize::MAX;
        assert!(fits_within_2x(m, m));
        assert!(fits_within_2x(m, m / 2 + 1));
        assert!(!fits_within_2x(m, m / 2));
        assert!(!fits_within_2x(m, 0));
    }
    #[test]
    fn reuse_and_explicit_wrapping() {
        let mut out = Vec::with_capacity(64);
        out.extend_from_slice(&[9, 8, 7]);
        let capacity = out.capacity();
        map_reusing(&[0, 1, u32::MAX], &mut out).unwrap();
        assert_eq!(out, [1, 4, u32::MAX - 1]);
        assert_eq!(out.capacity(), capacity);
        map_reusing(&[], &mut out).unwrap();
        assert!(out.is_empty());
        assert_eq!(out.capacity(), capacity);
        map_reusing(&vec![3; 257], &mut out).unwrap();
        assert_eq!(out, vec![10; 257]);
    }
    #[test]
    #[should_panic]
    fn affine_rejects_truncation() { affine(&[1, 2], &mut [0]); }
    #[test]
    fn ordering_and_scan() {
        assert_eq!(argmin_first(&[]), None);
        assert_eq!(argmin_first(&[u32::MAX; 9]), Some(0));
        assert_eq!(argmin_first(&[8, 3, 3, 9]), Some(1));
        let mut values = [u32::MAX, 1, u32::MAX, 5, 9];
        prefix_sum_wrapping(&mut values);
        assert_eq!(values, [u32::MAX, 0, u32::MAX, 4, 13]);
    }
    #[test]
    fn histograms_preserve_collisions() {
        for n in 0..1025 {
            let input: Vec<u8> = (0..n).map(|i| ((i * 137) % 256) as u8).collect();
            let mut expected = [0; 256];
            for &x in &input { expected[usize::from(x)] += 1; }
            assert_eq!(histogram4(&input), expected);
            let mut expected = [0; 256]; expected[255] = n as u64;
            assert_eq!(histogram4(&vec![255; n]), expected);
        }
    }
    #[test]
    fn byte_search_backends_boundaries_and_offsets() {
        for n in 0..130 {
            for offset in 0..64 {
                let storage: Vec<u8> = (0..n + offset).map(|i| ((i * 149) % 256) as u8).collect();
                let input = &storage[offset..];
                for key in [0, 1, 127, 128, 254, 255] {
                    let expected = find_byte_scalar(input, key);
                    assert_eq!(find_byte(input, key), expected);
                    #[cfg(target_arch = "x86_64")]
                    {
                        // SAFETY: x86-64 baseline and guarded optional feature.
                        assert_eq!(unsafe { find_byte_sse2(input, key) }, expected);
                        if std::is_x86_feature_detected!("avx2") {
                            assert_eq!(unsafe { find_byte_avx2(input, key) }, expected);
                        }
                    }
                    #[cfg(target_arch = "aarch64")]
                    if std::arch::is_aarch64_feature_detected!("neon") {
                        // SAFETY: guarded optional backend.
                        assert_eq!(unsafe { find_byte_neon(input, key) }, expected);
                    }
                }
            }
        }
        for n in [15, 16, 17, 31, 32, 33, 65] {
            for index in 0..n {
                let mut input = vec![0; n]; input[index] = 255;
                assert_eq!(find_byte(&input, 255), Some(index));
            }
            assert_eq!(find_byte(&vec![255; n], 255), Some(0));
        }
    }
    #[test]
    fn log_sampled_error_not_a_proof() {
        let z = 1.0f64 / 3.0;
        let truncation = 2.0 * std::f64::consts::LOG2_E * z.powi(11) / (11.0 * (1.0 - z * z));
        for x in 1..=65536u32 {
            let error = (log2_u32_teaching(NonZeroU32::new(x).unwrap()) - f64::from(x).log2()).abs();
            assert!(error <= truncation + 1e-12);
        }
        for k in 0..32 {
            assert_eq!(log2_u32_teaching(NonZeroU32::new(1 << k).unwrap()), f64::from(k));
        }
    }
}
