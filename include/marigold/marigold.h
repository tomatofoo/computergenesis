#ifndef MARIGOLD_H
#define MARIGOLD_H

#include "modules/utils.h"
#include <SDL2/SDL.h>

struct game {
    SDL_Window* window;
    SDL_Renderer* renderer;
    SDL_Surface* surface;
    strmap_t* images;
    strmap_t* sounds;
};

struct game* game_create(struct game* game);
void game_destroy(struct game* game);


#endif

