#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <math.h>
#include <stdio.h>


typedef struct limit {
    int16_t istart;
    int16_t iend;
} limit_t;

int8_t
limit_cmp(limit_t limit1, limit_t limit2) {
    if (limit1.istart == limit2.istart) {
        if (limit1.iend < limit2.iend) {
            return -1;
        }
        else if (limit1.iend == limit2.iend) {
            return 0;
        }
        else {
            return 1;
        }
    }
    if (limit1.istart < limit2.istart) {
        return -1;
    }
    else {
        return 1;
    }
}

typedef struct limits {
    size_t icapacity;
    size_t iamount;
    struct limit iarr[];
} limits_t;

limits_t*
limits_new(size_t capacity) {
    limits_t* limits = malloc(sizeof(limits_t) + capacity * sizeof(limit_t));
    if (limits == NULL) {
        return NULL;
    }

    limits->icapacity = capacity;
    limits->iamount = 0;
    limits_reset(limits);

    return limits;
}

void limits_destroy(limits_t* limits) {
    free(limits);
}

void limits_reset(limits_t* limits) {
    memset(limits->iarr, 0, limits->icapacity * sizeof(limit_t));
}

void limitsi_reset_amount(limits_t* limits) {
    memset(limits->iarr, 0, limits->iamount * sizeof(limit_t));
}

bool limits_add(limits_t* limits, int16_t start, int16_t end) {
    if (limits->iamount >= limits->icapacity) {
        return false;
    }

    limit_t limit = {
        .istart = start,
        .iend = end,
    };
    
    limit_t arr[limits->iamount + 1];
    // copy elements to arr
    for (size_t i = 0; i <= limits->iamount; i++) {
        arr[i] = limits->iarr[i];
    }
    limit_t item;
    limitsi_reset_amount(limits);

    /* three-step insertion */
    size_t dex;
    for (size_t i = 0; i <= limits->iamount; i++) { /* find dex */
        item = arr[i];
        if (i >= limits->iamount || limit_cmp(limit, item) < 1) {
            dex = i;
            break;
        }
    }
    if (dex < limits->iamount) { /* avoid unnecessary shifting */
        for (size_t i = limits->iamount; i > dex; i--) { /* shift elements */
            arr[i] = arr[i - 1];
        }
    }
    arr[dex] = limit; /* insert */
    limits->iamount++;

    /* add initial limit */
    limits->iarr[0] = arr[0];
    /* condense ranges */
    size_t cur = 0; /* current index in new array */
    for (size_t i = 1; i < limits->iamount; i++) {
        item = arr[i];
        if (limits->iarr[cur].iend >= item.istart - 1) {
            limits->iarr[cur].iend = fmax(
                limits->iarr[cur].iend,
                item.iend
            );
        }
        else {
            cur++;
            limits->iarr[cur] = item;
        }
    }
    limits->iamount = cur + 1;

    return true;
}

int main(int argc, char* argv[]) {
    limits_t* limits = limits_new(120);

    limits_add(limits, 1, 50);
    limits_add(limits, 45, 100);
    
    
    for (size_t i = 0; i < limits->iamount + 3; i++) {
        printf("start: %d\n", limits->iarr[i].istart);
        printf("end: %d\n", limits->iarr[i].iend);
        printf("---\n");
    }
    printf("---\n");
    printf("%d %d\n", limits->iamount, limits->icapacity);
    
    limits_add(limits, 102, 150);
    
    for (size_t i = 0; i < limits->iamount + 3; i++) {
        printf("start: %d\n", limits->iarr[i].istart);
        printf("end: %d\n", limits->iarr[i].iend);
        printf("---\n");
    }
    printf("---\n");
    printf("%d %d\n", limits->iamount, limits->icapacity);
    
    limits_destroy(limits);
}

