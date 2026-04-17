# 3D Graph Visualization Research

Research into existing open-source tools for interactive 3D graph visualization, for use in roadmap tooling.

## Requirement

A three-dimensional graph that can be manipulated (rotate, zoom, drag nodes), suitable for visualizing a roadmap with nodes and edges. macOS preferred.

---

## Top Options

### 1. 3d-force-graph ⭐ Recommended
JS/Three.js, MIT licensed, actively maintained. Full 3D drag/rotate/zoom with force-directed physics simulation. Easily embedded in Electron or a WKWebView. Most natural fit for a manipulable roadmap graph.

- GitHub: https://github.com/vasturiano/3d-force-graph
- npm: https://www.npmjs.com/package/3d-force-graph
- Live demo: https://vasturiano.github.io/3d-force-graph/

### 2. React Force Graph
Wrapper around 3d-force-graph as a React component. Same capabilities, better if building a React app.

### 3. Three.js (direct)
Lower-level WebGL engine — 3d-force-graph is built on it. MIT licensed, maximum control, but more development effort.

### 4. Gephi
Java cross-platform desktop app. Good for analysis and large graphs (50K+ nodes) but 3D interactivity is weak.

### 5. Cytoscape.js
Strong 2D with rich plugin ecosystem. Less suited for 3D but excellent for complex interaction patterns and custom styling.

---

## Recommended Approach (macOS native)

No strong native Swift/ObjC 3D graph library exists. Best path is either:
- **Swift app + WKWebView** hosting a 3d-force-graph scene
- **Electron app** with 3d-force-graph embedded directly
