"""Build .98 with an uninterrupted, counted assembly sound kernel."""
import build_tile_stream

if __name__ == '__main__':
    build_tile_stream.main(continuous_sound=True)
