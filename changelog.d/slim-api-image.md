### Changed

- **The API image is built in two stages and drops 62 % of its weight.**
  `api/Dockerfile` now installs into a builder stage and copies only the
  finished venv into a clean runtime stage, mirroring the shape `app/Dockerfile`
  has always used. Two layers carried the old 584.8 MB: 212 MB of apt packages —
  `build-essential`, which never compiled anything because all 88 packages in
  `uv.lock` ship wheels, and `libgl1`, installed for an OpenCV this project
  deliberately does not depend on — and 150.9 MB from a `chown -R` that ran
  after the venv was in place and so rewrote every file into a second layer.
  `COPY --chown` sets the ownership while the layer is written instead. Expected
  result is ~222 MB, which is 62 % less Artifact Registry growth per deploy and
  a shorter deploy rollout; the user-visible cold start was already bought away
  by the min-instance, so this is a cost and rollout change, not a latency one.
  Measured in Cloud Build against the serving image: 1.61 GB to 531 MB (#473).
