# PCB

Reserved for editable layout sources and deliberate fabrication releases.
Select the CAD tool and board constraints after schematic and mechanical review.

Resolve the optical aperture/lens height, magnet positions, actuator mounts and
USB connector placement before routing. Review USB routing, switching-current
returns, analog noise, thermal paths, driver bulk capacitors and test access.

The custom button coils mount in the mechanical assembly and connect to the PCB;
the design does not call for PCB spiral actuators. Reserve separate sensing and
actuator magnet zones based on the measured button fixture. Select DRV8231A
packages/footprints and an assembly supplier's exact part numbers before routing.

Each fabrication release should include source revision, stackup, design rules,
ERC/DRC results, Gerbers/drill files, assembly drawings and a revision-matched BOM.
There are no manufacturing files in this repository yet.
