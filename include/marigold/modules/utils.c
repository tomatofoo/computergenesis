#include "utils.h"

#include <stdlib.h>
#include <stddef.h>
#include <stdbool.h>
#include <stdio.h>
#include <assert.h>
#include <string.h>

/* simple, fast FNV1a hash */
unsigned int 
fnv1a32(const char* str) {
    unsigned int hash = 2166136261;

    /* iterate until null terminator */
    int chr;
    while (chr = *str++) {
        hash ^= chr;
        hash *= 16777619;
    }

    return hash;
}

/* credit to https://benhoyt.com/writings/hash-table-in-c/ */
/* Variable-sized hashmp with string keys */

strmap_t* 
strmap_new(size_t capacity) {
    strmap_t* map = malloc(sizeof(strmap_t));
    if (map == NULL) {
        return NULL;
    }

    map->icapacity = capacity;
    map->iarr = calloc(capacity, sizeof(strmap_item_t));
    /* original map malloc succeeded, but arr calloc failed */
    if (map->iarr == NULL) { 
        free(map);
        return NULL;
    }

    return map;
}

void 
strmap_destroy(strmap_t* map) {
    /* free keys allocated with strdup */
    for (size_t i = 0; i < map->icapacity; i++) {
        free(map->iarr[i].ikey);
    }

    free(map->iarr);
    free(map);
}

void*
strmap_get(strmap_t* map, const char* key) {
    size_t index = fnv1a32(key) % map->icapacity;
    while (map->iarr[index].ikey != NULL) {
        if (strcmp(map->iarr[index].ikey, key) == 0) {
            return map->iarr[index].ivalue;
        }
        index = (index + 1) % map->icapacity;
    }
    return NULL;
}

/* does not return NULL because size will always be adequate */
void
strmapi_set(strmap_item_t* arr,
            size_t capacity,
            const char* key,
            void* value) {
    /* Bitwise AND is faster than modulus, but the modulus is the proper way */
    size_t index = fnv1a32(key) % capacity;
    while (arr[index].ikey != NULL) {
        /* chosen over putting in while statement because it doesn't set the 
         * key when it's already been set 
         */
        if (strcmp(arr[index].ikey, key) == 0) {
            arr[index].ivalue = value;
            return;
        }
        index = (index + 1) % capacity;
    }
    
    arr[index].ikey = strdup(key);
    arr[index].ivalue = value;
}

bool
strmap_set(strmap_t* map, const char* key, void* value) {
    assert(key != NULL);

    if (map->ilength >= map->icapacity / 2) {
        if (!strmap_expand(map)) {
            return false;
        }
    }

    strmapi_set(map->iarr, map->icapacity, key, value);
    map->ilength++;
    return true;
}

bool 
strmap_expand(strmap_t* map) {
    size_t capacity = map->icapacity * 2;
    if (capacity < map->icapacity) { /* overflow */
        return false;
    }

    strmap_item_t* arr = calloc(capacity, sizeof(strmap_item_t));
    if (arr == NULL) {
        return false;
    }

    for (int i = 0; i < map->icapacity; i++) {
        if (map->iarr[i].ikey != NULL) {
            /* does the modulus with the new capacity */
            strmapi_set(arr, capacity, map->iarr[i].ikey, map->iarr[i].ivalue);
        }
    }

    free(map->iarr);
    map->iarr = arr;
    map->icapacity = capacity;
    return true;
}

void* strmap_pop(strmap_t* map, const char* key) {
    assert(key != NULL);

    size_t index = fnv1a32(key) % map->icapacity;
    while (map->iarr[index].ikey != NULL) {
        if (strcmp(map->iarr[index].ikey, key) == 0) {
            free(map->iarr[index].ikey);
            void* value = map->iarr[index].ivalue;
            map->iarr[index].ikey = NULL; /* not accessing a freed value */
            map->iarr[index].ivalue = NULL;

            return value;
        }
        index = (index + 1) % map->icapacity;
    }

    return NULL;
}

size_t
strmapa_capacity(strmap_t* map) {
    return map->icapacity;
}

size_t 
strmapa_length(strmap_t* map) {
    return map->ilength;
}

int 
main() {
    strmap_t* map = strmap_new(64);

    strmap_set(map, "key", "value");

    printf("%d\n", strmapa_capacity(map));
    printf("%d\n", strmapa_length(map));
    
    strmap_destroy(map);
}

