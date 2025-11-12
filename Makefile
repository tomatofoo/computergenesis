CC=gcc-15
CFLAGS=-fms-extensions $$(pkg-config --cflags --libs glib-2.0 gsl sdl2 sdl2_image sdl2_mixer)
M=modules
O=macho

ENTITIES_I=$(M)/entities.c
ENTITIES_H=$(M)/entities.h
ENTITIES_O=$(O)/entities.o

LEVEL_I=$(M)/level.c
LEVEL_H=$(M)/level.h
LEVEL_O=$(O)/level.o

RENDERER_I=$(M)/renderer.c
RENDERER_H=$(M)/renderer.h
RENDERER_O=$(O)/renderer.o

MODULES_I=$(ENTITIES_I) $(LEVEL_I) $(RENDERER_I) $(ENTITIES_H) $(LEVEL_H) $(RENDERER_H)
MODULES_O=$(ENTITIES_O) $(LEVEL_O) $(RENDERER_O)

MAIN_I=main.c
MAIN_O=$(O)/main.o

LINK_I=$(MODULES_O) $(MAIN_O)
LINK_O=main

all: $(MODULES_O) $(MAIN_O) $(LINK_O)

$(MODULES_O): $(MODULES_I)
	$(CC) $(ENTITIES_I) -c -o $(ENTITIES_O) $(CFLAGS)
	$(CC) $(LEVEL_I) -c -o $(LEVEL_O) $(CFLAGS)
	$(CC) $(RENDERER_I) -c -o $(RENDERER_O) $(CFLAGS)

$(MAIN_O): $(MAIN_I)
	$(CC) $(MAIN_I) -c -o $(MAIN_O) $(CFLAGS)

$(LINK_O): $(LINK_I)
	$(CC) $(LINK_I) -o $(LINK_O) $(CFLAGS)

clean:
	trash $(LINK_I) $(LINK_O)

