# Frozen simulation inputs

These three XML netlists are byte-identical copies of the historical bench
package inputs used for the brake study. Their hashes and original path labels
remain in `../results/inventory.json`. They do not represent the current PCB
revision. Keeping them here makes the study reproducible without restoring an
obsolete board package.

`baseline.json` records the historical PCB/panel and supplier-archive hashes at
commit `145d2be`. The review verifies those objects in Git and the retained
supplier archive on disk. A shallow clone needs that commit fetched for this
provenance check. The existing numerical results and their original evidence
files have been preserved; the code relocation does not rerun the simulation.
