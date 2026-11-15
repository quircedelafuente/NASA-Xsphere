import numpy as np
from processing.spectrum import aperture


def test_aperture_recovers_point_source_on_flat_background():
    yy, xx = np.indices((19, 19))
    star = 1000 * np.exp(-((xx - 9.3) ** 2 + (yy - 8.8) ** 2) / (2 * 0.64 ** 2))   # FWHM 1.5 px
    f, e = aperture(star + 5.0, np.ones_like(star), 9.3, 8.8)
    assert abs(f - star.sum()) / star.sum() < 0.02 and e > 0
    star[9, 9] = np.nan                                                             # bad pixel in the aperture → no point
    assert np.isnan(aperture(star, np.ones_like(star), 9.3, 8.8)[0])
