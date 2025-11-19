#include "modules/entities.h"
#include "modules/level.h"
#include "modules/renderer.h"
#include "modules/utils.h"
#include "marigold.h"

#include <SDL2/SDL.h>

#include <stdio.h>

struct game* game_create(char* title,
                         int width,
                         int height,
                         int pixel_width,
                         int pixel_height) {

    struct game* game = malloc(sizeof(struct game));
    if (!game) {
        return NULL;
    }

    game->window = SDL_CreateWindow(
        title,
        SDL_WINDOWPOS_UNDEFINED,
        SDL_WINDOWPOS_UNDEFINED,
        width,
        height,
        0
    );
    if (!game->window) {
        free(game);
        return NULL;
    }

    game->renderer = SDL_CreateRenderer(game->window, -1, 0);
    if (!game->renderer) {
        SDL_DestroyWindow(game->window);
        free(game);
        return NULL;
    }

    game->surface = SDL_CreateRGBSurface(
        0,
        width / pixel_width,
        height / pixel_height,
        32,
        0, 0, 0, 0
    );
    if (!game->surface) {
        SDL_DestroyWindow(game->window);
        SDL_DestroyRenderer(game->renderer);
        free(game);
        return NULL;
    }

    return game;
}


void game_destroy(struct game* game) {
    SDL_DestroyWindow(game->window);
    SDL_DestroyRenderer(game->renderer);
    SDL_FreeSurface(game->surface);
    free(game);
}

