from .player import BuzzerPlayer


def get_melody_catalog():
	from .melodies import MELODY_CATALOG

	return MELODY_CATALOG


__all__ = ["BuzzerPlayer", "get_melody_catalog"]

