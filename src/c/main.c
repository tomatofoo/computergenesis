#include <stdio.h>
#include <stdbool.h>
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>

#define WINDOW_TITLE "Computergenesis"
#define WINDOW_WIDTH 800
#define WINDOW_HEIGHT 640

// Structs
struct Game {
    SDL_Window *window;
    SDL_Renderer *renderer;
};

// Function Prototypes
int init(struct Game *game);
void cleanup(struct Game *game);
void loop(struct Game *game);

// Main
int main(int argc, char *argv[]) {
    struct Game game = {
        .window = NULL,
        .renderer = NULL,
    };
    if (init(&game)) {
        cleanup(&game);
        return 1;
    }

    loop(&game); // Main loop

    printf("Exiting...\n");
    cleanup(&game);

    return 0;
}

// Prototyped Functions
int init(struct Game *game) {
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

    return 0;
}

void cleanup(struct Game *game) {
    SDL_DestroyWindow(game->window);
    SDL_DestroyRenderer(game->renderer);
    SDL_Quit();
}

void loop(struct Game *game) {
    // Main Loop
    SDL_Event event;
    bool running = true;

    while (running) {
        // Events
        while (SDL_PollEvent(&event)){
            switch (event.type) {
                case SDL_QUIT:
                    running = false;
                    break;
            }
        }

        // Rendering
        SDL_RenderClear(game->renderer);
        SDL_RenderPresent(game->renderer);
    }
}

