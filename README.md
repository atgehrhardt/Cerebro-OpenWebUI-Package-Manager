# Cerebro-OpenWebUI-Package-Manager

## Introduction
The **Cerebro-OpenWebUI-Package-Manager** is a comprehensive package management tool designed for the Cerebro OpenWebUI framework. It simplifies the process of managing packages, ensuring seamless integration of GUI applets and additional functionality.

## Features
- **Easy Installation and Uninstalling**: Streamline the process of installing and uninstalling packages
- **User-Friendly Interface**: Intuitive and accessible interface for managing packages
- **LLM-Powered Tool Launcher**: Allow LLMs to invoke tools, even without function calling ability (Cerebro Tool Launcher)

## Installation
- Ensure you are using OpenWebUI version 0.3.6 or later
- In OpenWebUI navigate to Workspace => Functions => Import Functions
- Import `cerebro_package_manager.json` and `cerebro_tool_launcher.json` from the `src` directory in this repo
- Change the default config options from the gui if needed
- Enable globally or on a per-model basis

### Usage
- **List installed packages**: 
    `owui list`

- **Install a package**: 
    `owui install <package_name>`

- **Remove a package**: 
    `owui uninstall <package_name>`

- **Run a package**: 
    `owui run <package_name>`

## Roadmap
- [ ] Package versioning and Update commands
- [ ] Require version numbers

## Bugs
- [ ] Uninstalling is not properly removing the actual directory from files - Working on fix

## Contributing
Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes.
4. Commit your changes (`git commit -am 'Add some feature'`).
5. Push to the branch (`git push origin feature-branch`).
6. Create a new Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.