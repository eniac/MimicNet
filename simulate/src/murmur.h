#pragma once

#include "INETDefs.h"

uint32_t murmur3_32(const uint8_t* key, size_t len, uint32_t seed);
int positiveMod(int value, int modulus);
