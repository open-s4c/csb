/*
 * Copyright (C) Huawei Technologies Co., Ltd. 2026. All rights reserved.
 * SPDX-License-Identifier: MIT
 */
#ifndef BM_HELPER_H
#define BM_HELPER_H

#include "compiler.h"
#include "rand.h"
#include <stdbool.h>
#include <stdint.h>

static inline size_t bm_generate_noise_interruptible(size_t max_noise,
                                                     bool random,
                                                     bool (*stop)(void)) {
  size_t i = 0;
  size_t nop_count = max_noise;

  if (max_noise == 0)
    return 0;

  if (random) {
    nop_count = random_thread_safe_get_next(0, max_noise);
  }

  barrier();
  for (i = 0; i < nop_count && !stop(); i++) {
    __asm__ __volatile__("nop");
  }
  barrier();

  return nop_count;
}

static inline size_t bm_generate_noise(size_t max_noise, bool random) {
  size_t i = 0;
  size_t nop_count = max_noise;

  if (max_noise == 0)
    return 0;

  if (random) {
    nop_count = random_thread_safe_get_next(0, max_noise);
  }

  barrier();
  for (i = 0; i < nop_count; i++) {
    __asm__ __volatile__("nop");
  }
  barrier();

  return nop_count;
}

#endif
