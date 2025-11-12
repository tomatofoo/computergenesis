#include "modules/entities.h"
#include "modules/level.h"
#include "modules/renderer.h"

#include <stdio.h>
#include <stdbool.h>

#include <glib.h>
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>

#define WINDOW_TITLE "Computergenesis"
#define WINDOW_WIDTH 960
#define WINDOW_HEIGHT 720
#define SURFACE_WIDTH 320
#define SURFACE_HEIGHT 240

#define ADD_IMG(game, key, img) g_hash_table_insert(game->images, key, img)
#define IMG(game, key) g_hash_table_lookup(game->images, key)
#define ADD_SOUND(game, key, sound) g_hash_table_insert(game->sounds, key, sound)
#define SOUND(game, key) g_hash_table_lookup(game->sounds, key)

struct Game {
    SDL_Window *window;
    SDL_Renderer *renderer;
    SDL_Surface *surface;
    GHashTable *images;
    GHashTable *sounds;
};

int init(struct Game* game);
void cleanup(struct Game* game);
void loop(struct Game* game);
void free_img(void* img);

int main(int argc, char** argv) {
    struct Game game = {
        .window = NULL,
        .renderer = NULL,
        .surface = NULL,
        .images = NULL,
        .sounds = NULL,
    };
    if (init(&game)) {
        cleanup(&game);
        return 1;
    }

    loop(&game);

    printf("Exiting...\n");
    cleanup(&game);

    return 0;
}

int init(struct Game* game) {
    if (SDL_Init(SDL_INIT_EVERYTHING)) {
        fprintf(stderr, "Error initializing SDL: %s\n", SDL_GetError());
        return 1;
    }

    game->window = SDL_CreateWindow(
        WINDOW_TITLE,
        SDL_WINDOWPOS_CENTERED,
        SDL_WINDOWPOS_CENTERED,
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

    /* Images */
    game->images = g_hash_table_new_full(NULL, NULL, NULL, free_img);
    ADD_IMG(game, "redbrick", IMG_Load("data/images/redbrick.png"));
    ADD_IMG(game, "greystone", IMG_Load("data/images/greystone.png"));
    
    return 0;
}

void cleanup(struct Game* game) {
    SDL_DestroyWindow(game->window);
    SDL_DestroyRenderer(game->renderer);
    SDL_FreeSurface(game->surface);

    g_hash_table_destroy(game->images);
       
    SDL_Quit();
}

void loop(struct Game* game) { /* Main Loop */
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

void free_img(void *img) {
    SDL_FreeSurface(img);
}

