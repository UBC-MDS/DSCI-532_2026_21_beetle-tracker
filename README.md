# DSCI-532_2026_21_beetle-tracker

## Japanese Beetle — Invasive Species Tracker

A Python Shiny dashboard for tracking Japanese Beetle observations across the world.

### Shiny App URL

There are 2 builds. The stable build (main) is the official release, and is manually republished when necessary. The preview build (dev) rebuilds automatically on every push to the dev branch. The preview build also functions as the team's live preview, so anyone can see the latest state of the app without running it locally.

[Stable](https://019c9184-1261-a87a-ddfc-1564bfdd2990.share.connect.posit.cloud)

[Preview](https://019c9188-e172-6a48-02c5-6482db896430.share.connect.posit.cloud)

## Running the App Locally

### 1. Clone the repository

```bash
git clone https://github.com/UBC-MDS/DSCI-532_2026_21_beetle-tracker.git
cd DSCI-532_2026_21_beetle-tracker
```

### 2. Create the conda environment

```bash
conda env create -f environment.yml
```

> If the environment already exists, remove it first:
>
> ```bash
> conda env remove -n dsci532
> ```

### 3. Activate the environment

```bash
conda activate dsci532
```

### 4. Start the dashboard

```bash
shiny run src/app.py
```

Open the URL provided in the terminal output to view the app in your browser.

## AI Explorer Tab

The **AI Explorer** tab requires an API key to function. The rest of the dashboard works without one.

The easiest (and free) option is a **GitHub Personal Access Token (PAT)**, which you can generate at [github.com/settings/tokens](https://github.com/settings/tokens).

Alternatively, an **Anthropic API key** also works.

### Setting up your API key

Create a file named `.env` in the root of the repository (next to `environment.yml`):

```text
DSCI-532_2026_21_beetle-tracker/
├── .env               <- create this file
├── environment.yml
├── src/
...
```

Add one of the following to the `.env` file:

```bash
# Option 1: GitHub PAT (free)
GITHUB_PAT=your_github_pat_here

# Option 2: Anthropic API key
ANTHROPIC_API_KEY=your_anthropic_key_here
```

If both are present, the GitHub PAT takes priority. The `.env` file is listed in `.gitignore` and will not be committed.
