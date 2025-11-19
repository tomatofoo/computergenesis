#include <marigold/marigold.h>

#include <SDL2/SDL.h>

#include <stdio.h>

int main() {
}

int init(struct game* game) {
    if (SDL_Init(SDL_INIT_EVERYTHING)) {
        fprintf(stderr, "Error initializing SDL: %s\n", SDL_GetError());
        return 1;
    }

    game->window = SDL_CreateWindow(
        WINDOW_TITLE,
        SDL_WINDOWPOS_UNDEFINED,
        SDL_WINDOWPOS_UNDEFINED,
        WINDOW_WIDTH,
        WINDOW_HEIGHT,
        0
    );
    if (!game->window) {
        fprintf(stderr, "Error creating window: %s\n", SDL_GetError());
        return 1;
    }

    game->renderer = SDL_CreateRenderer(game->window, -1, 0);
    if (!game->renderer) {
        fprintf(stderr, "Error creating renderer: %s\n", SDL_GetError());
        return 1;
    }
    
    game->surface = SDL_CreateRGBSurface(
        0,
        SURFACE_WIDTH,
        SURFACE_HEIGHT,
        32,
        0, 0, 0, 0
    );
    if (!game->surface) {
        fprintf(stderr, "Error creating surface: %s\n", SDL_GetError());
        return 1;
    }

    return 0;
}

void loop(struct game* game) { /* Main Loop */
    SDL_Event event;
    const unsigned char* keys = SDL_GetKeyboardState(NULL);
    SDL_Texture* texture;
    bool running = true;

    while (running) {

        /* Events */
        while (SDL_PollEvent(&event)){
            switch (event.type) {
                case SDL_QUIT:
                    running = false;
                    break;
            }
        }
        
        /* Rendering */ 
        SDL_SetRenderDrawColor(game->renderer, 0, 0, 0, SDL_ALPHA_OPAQUE);
        SDL_RenderClear(game->renderer);
        
        texture = SDL_CreateTextureFromSurface(game->renderer, game->surface);
        SDL_RenderCopy(game->renderer, texture, NULL, NULL);
        SDL_RenderPresent(game->renderer);
    }

    /* Clean up local variables */ 
    SDL_DestroyTexture(texture);
}

