# Blueprint Text Toolkit

**Turn noisy Unreal Engine Blueprint text exports into cleaner, more readable text — without AI.**

Blueprint Text Toolkit is a Python desktop application designed to make Unreal Engine Blueprint text exports easier to inspect, understand, and work with.

Blueprint exports can contain a large amount of editor-related information, identifiers, node positions, pin metadata, and connection data. This can make the actual logic difficult to read.

This tool aims to reduce that noise and present the useful information in a more structured format.


### Windows application

Download the latest Windows executable:

[**Download Blueprint Text Toolkit for Windows**](https://github.com/MustiKlas/Blueprint-Text-Toolkit/releases/latest/download/BlueprintTextToolkit.exe)

No Python installation is required to run the packaged Windows application.

For source code and previous releases, visit the [Releases](../../releases) page.


## Features

- Process copied or exported Unreal Engine Blueprint text.
- Reduce unnecessary editor-related information.
- Generate cleaner, more readable textual representations.
- Present node and pin information.
- Preserve relevant connection information for understanding Blueprint logic.
- Provide multiple output formats.
- Work locally without requiring an AI service or API key.

## Why this project?

Blueprint graphs can be difficult to inspect as raw text. A significant portion of an exported Blueprint representation may consist of metadata rather than the logic developers want to examine.

Blueprint Text Toolkit aims to make that information easier to work with through deterministic Python-based processing.

The project is also intended to help developers prepare Blueprint logic for code review, documentation, analysis, and potential C++ refactoring workflows.

## Screenshots

<img width="1911" height="1021" alt="Ekran görüntüsü 2026-11-02 221126" src="https://github.com/user-attachments/assets/1e8e99c7-3d47-4bff-8b2c-d557118b5820" />
<img width="1911" height="1021" alt="Ekran görüntüsü 2026-11-02 221126" src="https://github.com/user-attachments/assets/a0d24030-b174-428c-96fb-12b0cd681690" />
<img width="1911" height="1021" alt="Ekran görüntüsü 2026-11-02 221126" src="https://github.com/user-attachments/assets/37a4e77f-4d6a-43fb-85cc-c385faf358a9" />


## Getting Started

### Windows application

Download the latest Windows release from the [Releases](../../releases) page.

Extract the downloaded archive if necessary and launch the application.

> Windows builds will be provided through GitHub Releases once the packaged application has been tested.

### Run from source

Requirements:

- Python (the supported version will be specified after release testing).
- Git (optional, for cloning the repository).

Clone the repository:

```bash
git clone https://github.com/MustiKlas/Blueprint-Text-Toolkit.git
cd Blueprint-Text-Toolkit
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python main.py
```

## Usage

1. Open Blueprint Text Toolkit.
2. Provide your Unreal Engine Blueprint text export.
3. Choose the desired output format.
4. Generate and inspect the processed result.

The exact available output formats and supported Blueprint structures may evolve as the project develops.

## Project Structure

```text
BlueprintTextToolkit/
├── app/
├── data/
├── tests/
├── main.py
├── README.md
├── LICENSE
├── requirements.txt
└── .gitignore
```

## Testing

The project includes automated tests.

Run them with:

```bash
pytest
```

## Limitations

- The tool processes textual Blueprint exports; it does not directly open or modify Unreal Engine project files.
- It does not connect to Unreal Engine.
- It does not use AI to interpret or transform Blueprint logic.
- Supported node types and export structures depend on the parser implementation and may expand over time.

## Contributing

Contributions, bug reports, and feature suggestions are welcome.

If you encounter an issue, please open a GitHub Issue and include a sample Blueprint export when possible. Remove private project information before sharing samples.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Disclaimer

Blueprint Text Toolkit is an independent community project and is not affiliated with, endorsed by, or sponsored by Epic Games.

Unreal Engine is a trademark of Epic Games, Inc.
