#pragma once
#ifndef LEVEL_H
#define LEVEL_H

#include <SDL2/SDL.h>

#define COLUMN_RECT(surf, index) &(SDL_Rect){index, 0, 1, surf->h}

#endif

