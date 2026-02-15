This folder contains a PlantUML source for the project's class diagram.

Files:
- architecture.puml : PlantUML source for the class diagram.

Render options (pick one):

1) VS Code + PlantUML extension
- Install `PlantUML` extension and view `architecture.puml` preview.

2) Local Java + PlantUML jar
- Download `plantuml.jar` (https://plantuml.com/download)
- Run (from repo root):

```bash
java -jar path/to/plantuml.jar docs/architecture.puml
```

This produces `docs/architecture.png` (or multiple formats if requested).

3) Docker (no install of Java):

```bash
docker run --rm -v "%CD%":/workspace plantuml/plantuml -tpng docs/architecture.puml
```

Notes:
- PlantUML is a text format; editing `docs/architecture.puml` updates the diagram.
- If you want, I can render a PNG/SVG here and add it to the repo — tell me which format you prefer and whether to commit it to `docs/`.
