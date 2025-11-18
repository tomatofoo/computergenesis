#pragma once
#ifndef UTILS_H
#define UTILS_H

#include <stddef.h>
#include <stdbool.h>

typedef struct strmap_item strmap_item_t;
typedef struct strmap strmap_t;

unsigned int fnv1a32(const char* str);

strmap_t* strmap_new(size_t capacity);
void strmap_destroy(strmap_t* map);
void* strmap_get(strmap_t* map, const char* key);
bool strmap_set(strmap_t* map, const char* key, void* value);
bool strmap_expand(strmap_t* map);
size_t strmapa_capacity(strmap_t *map);
size_t strmapa_length(strmap_t *map);

#endif

