CC=gcc-15
CFLAGS=-Ilib -fms-extensions $$(pkg-config --cflags --libs gsl sdl2 sdl2_image sdl2_mixer)
L_D=lib
O_D=macho

# Marigold
MARIGOLD_L_D=$(L_D)/marigold
MARIGOLD_M_D=$(MARIGOLD_L_D)/modules
MARIGOLD_O_D=$(O_D)/marigold

MARIGOLD_ENTITIES_I=$(MARIGOLD_M_D)/entities.c
MARIGOLD_ENTITIES_H=$(MARIGOLD_M_D)/entities.h
MARIGOLD_ENTITIES_O=$(MARIGOLD_O_D)/entities.o

MARIGOLD_LEVEL_I=$(MARIGOLD_M_D)/level.c
MARIGOLD_LEVEL_H=$(MARIGOLD_M_D)/level.h
MARIGOLD_LEVEL_O=$(MARIGOLD_O_D)/level.o

MARIGOLD_RENDERER_I=$(MARIGOLD_M_D)/renderer.c
MARIGOLD_RENDERER_H=$(MARIGOLD_M_D)/renderer.h
MARIGOLD_RENDERER_O=$(MARIGOLD_O_D)/renderer.o

MARIGOLD_MODULES_I=$(MARIGOLD_ENTITIES_I) \
				   $(MARIGOLD_LEVEL_I) 	  \
				   $(MARIGOLD_RENDERER_I) \
				   $(MARIGOLD_ENTITIES_H) \
				   $(MARIGOLD_LEVEL_H)    \
				   $(MARIGOLD_RENDERER_H)

MARIGOLD_MODULES_O=$(MARIGOLD_ENTITIES_O) \
				   $(MARIGOLD_LEVEL_O)    \
				   $(MARIGOLD_RENDERER_O)

MARIGOLD_I=$(MARIGOLD_L_D)/marigold.c
MARIGOLD_H=$(MARIGOLD_L_D)/marigold.h
MARIGOLD_O=$(MARIGOLD_O_D)/marigold.o

# microui
MICROUI_L_D=$(L_D)/microui
MICROUI_O_D=$(O_D)/microui

MICROUI_I=$(MICROUI_L_D)/microui.c
MICROUI_H=$(MICROUI_L_D)/microui.h
MICROUI_O=$(MICROUI_O_D)/microui.o

# lib
LIB_I=$(MARIGOLD_I) \
	  $(MICROUI_I)  \
	  $(MARIGOLD_H) \
	  $(MICROUI_H)

LIB_O=$(MARIGOLD_O) \
	  $(MICROUI_O)

# main
MAIN_I=main.c
MAIN_O=$(O_D)/main.o

# Link
LINK_I=$(MARIGOLD_MODULES_O) \
	   $(LIB_O)              \
	   $(MAIN_O)

LINK_O=main

# Targets
all: $(LINK_I) $(LINK_O)

$(MARIGOLD_MODULES_O): $(MARIGOLD_MODULES_I)
	$(CC) $(MARIGOLD_ENTITIES_I) -c -o $(MARIGOLD_ENTITIES_O) $(CFLAGS)
	$(CC) $(MARIGOLD_LEVEL_I) -c -o $(MARIGOLD_LEVEL_O) $(CFLAGS)
	$(CC) $(MARIGOLD_RENDERER_I) -c -o $(MARIGOLD_RENDERER_O) $(CFLAGS)

$(LIB_O): $(LIB_I)
	$(CC) $(MARIGOLD_I) -c -o $(MARIGOLD_O) $(CFLAGS)
	$(CC) $(MICROUI_I) -c -o $(MICROUI_O) $(CFLAGS)

$(MAIN_O): $(MAIN_I)
	$(CC) $(MAIN_I) -c -o $(MAIN_O) $(CFLAGS)

$(LINK_O): $(LINK_I)
	$(CC) $(LINK_I) -o $(LINK_O) $(CFLAGS)

clean:
	trash $(LINK_I) $(LINK_O)

