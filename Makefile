main: main.c
	gcc main.c -o main $$(pkg-config --cflags --libs gsl sdl2 sdl2_image sdl2_mixer)

clean:
	trash main

