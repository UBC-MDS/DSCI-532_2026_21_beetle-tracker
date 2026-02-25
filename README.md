# DSCI-532_2026_21_beetle-tracker

## Japanese Beetle — Invasive Species Tracker

A Python Shiny dashboard for tracking Japanese Beetle observations across the world.

### Shiny App URL

There are 2 builds. The stable build (main) is the official release, and is manually republished when necessary. The preview build (dev) rebuilds automatically on every push to the dev branch. The preview build also functions as the team's live preview, so anyone can see the latest state of the app without running it locally.

[Stable](https://019c9184-1261-a87a-ddfc-1564bfdd2990.share.connect.posit.cloud)

[Preview](https://019c9188-e172-6a48-02c5-6482db896430.share.connect.posit.cloud)

## Running the App Locally

### 1. Create the conda environment

```bash
conda env create -f environment.yml
```

### 2. Activate the environment

```bash
conda activate dsci532
```

### 3. Start the dashboard

```bash
shiny run src/app.py
```

Open the URL provided in the terminal output to view the app in your browser.
