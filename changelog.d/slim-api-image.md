### Changed

- **The API image is built in two stages and drops two thirds of its weight.**
  `api/Dockerfile` now installs into a builder stage and copies only the
  finished venv into a clean runtime stage, mirroring the shape `app/Dockerfile`
  has always used. Two layers carried the bulk: an apt layer of 638 MB unpacked
  holding `build-essential`, which never compiled anything because all 88
  packages in `uv.lock` ship wheels, and `libgl1`, installed for an OpenCV this
  project deliberately does not depend on; and a second copy of the whole venv
  made by a `chown -R` that ran after the venv was already in place, where
  `COPY --chown` sets the ownership while the layer is written. Measured in
  Cloud Build with the same tool for both images, the old one pulled from the
  registry rather than estimated: 1.61 GB unpacked before, 531 MB after. That
  is less Artifact Registry growth per deploy and a shorter deploy rollout; the
  user-visible cold start was already bought away by the min-instance, so this
  is a cost and rollout change, not a latency one (#473).
