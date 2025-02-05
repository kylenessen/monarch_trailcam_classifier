# Monarch Trailcam Classifier Documentation

This branch contains the documentation website for the Monarch Trailcam Classifier project. The documentation is built using Jekyll and hosted on GitHub Pages.

## Local Development

To run this documentation site locally:

1. Install Ruby and Jekyll
```bash
# macOS (using Homebrew)
brew install ruby
gem install jekyll bundler

# Ubuntu/Debian
sudo apt-get install ruby-full build-essential
gem install jekyll bundler
```

2. Clone the repository and switch to the docs branch
```bash
git clone https://github.com/yourusername/monarch_trailcam_classifier.git
cd monarch_trailcam_classifier
git checkout docs
```

3. Run the site locally
```bash
bundle install
bundle exec jekyll serve
```

4. Open your browser to `http://localhost:4000/monarch_trailcam_classifier`

## Updating Documentation

1. Make changes to the markdown files
2. Commit and push to the docs branch
3. GitHub Pages will automatically rebuild the site

## Structure

- `_config.yml` - Jekyll configuration
- `index.md` - Main documentation page
- `images/` - Documentation images and assets