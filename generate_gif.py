import os
import imageio
import numpy as np

from core_lite.simulation import run_simulation
from visualization.network_plot import plot_network


OUTPUT_DIR = "frames"
GIF_NAME = "resonanzraum.gif"


def generate():

    # ------------------------------------------
    # Setup
    # ------------------------------------------
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # ------------------------------------------
    # Run both systems
    # ------------------------------------------
    G1, hist1, load1, edge1 = run_simulation(
        steps=20,
        stress_mode="constant",
        stress=0.15
    )

    G2, hist2, load2, edge2 = run_simulation(
        steps=20,
        stress_mode="increasing",
        stress=0.2
    )

    graphs1 = hist1["graphs"]
    graphs2 = hist2["graphs"]

    frame_paths = []

    # ------------------------------------------
    # Generate frames
    # ------------------------------------------
    for i in range(len(graphs1)):

        G1_t = graphs1[i]
        G2_t = graphs2[i]

        # Plot both systems
        fig1 = plot_network(G1_t, load1, edge1)
        fig2 = plot_network(G2_t, load2, edge2)

        # Add titles (important!)
        fig1.update_layout(
            title=dict(
                text="Stable System",
                y=0.92,           # Titel etwas nach unten ziehen
                x=0.5,
                xanchor="center"
            ),
            margin=dict(t=80)    # mehr Platz oben
        )

        fig2.update_layout(
            title=dict(
                text="Collapse System",
                y=0.92,
                x=0.5,
                xanchor="center"
            ),
            margin=dict(t=80)
        )

        # Save individual images
        f1 = f"{OUTPUT_DIR}/left_{i:03d}.png"
        f2 = f"{OUTPUT_DIR}/right_{i:03d}.png"

        fig1.write_image(f1)
        fig2.write_image(f2)

        # Read images
        img1 = imageio.imread(f1)
        img2 = imageio.imread(f2)

        # Combine side-by-side
        combined = np.hstack((img1, img2))

        combined_path = f"{OUTPUT_DIR}/frame_{i:03d}.png"
        imageio.imwrite(combined_path, combined)

        frame_paths.append(combined_path)

    # ------------------------------------------
    # Create GIF
    # ------------------------------------------
    images = [imageio.imread(p) for p in frame_paths]

    imageio.mimsave(GIF_NAME, images, duration=1.2)

    print(f"\n✅ GIF successfully created: {GIF_NAME}")


if __name__ == "__main__":
    generate()