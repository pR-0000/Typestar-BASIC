"""Build .101 with console head positioning, keeping .100 reproducible."""
import build_tile_stream

if __name__ == '__main__':
    build_tile_stream.main(continuous_sound=True, paper_grid=True,
                           release_audit=True, head_jog=True)
