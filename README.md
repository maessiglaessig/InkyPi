# InkyPi (Personal Edition)

<img src="./docs/images/inky_clock.jpg" />

**Note:** This repository is based on the original open-source project **InkyPi** by @faithak.
> Original repo: https://github.com/fatihak/InkyPi  
> This version is maintained independently and contains custom plugins and changes not intended for general public distribution.  
> All credit for the original framework and idea goes to the original authors.

## About This Version 
This project is a customized version of InkyPi, tailored for personal use.  
The main changes are:
- Additional plugins specific to my own needs (e.g., local event scraper for Zurich, movie recommendations, ai news summary, etc.)
- Minor adjustments to existing plugins and UI

It is not intended to replace or compete with the original project.  
If you are looking for a general-purpose, community-supported version, please visit the original repo instead.

**Features**:
- Natural paper-like aethetic: crisp, minimalist visuals that are easy on the eyes, with no glare or backlight
- Web Interface allows you to update and configure the display from any device on your network
- Minimize distractions: no LEDS, noise, or notifications, just the content you care about
- Easy installation and configuration, perfect for beginners and makers alike
- Open source project allowing you to modify, customize, and create your own plugins
- Set up scheduled playlists to display different plugins at designated times

**My Plugins**:

- AI RSS Summary: Generate a three sentence long AI news summary given certain rss feeds from various news sites (hardcoded prompt for my own application [will fix])
- Event and exhibits in Zurich: Displays a random cultural event or exhibition in Zurich
- Movie recommendations: Displays a movie with poster and plot summary from a list of movies the user inputs (WIP: user should be able to give one or two letterboxd usernames and the plugin then creates the list on its own)

Additional plugins coming soon! For documentation on building custom plugins, see [Building InkyPi Plugins](./docs/building_plugins.md).

## Hardware 
**Core Components:**
- Raspberry Pi (4 | 3 | Zero 2 W)
    - Recommended to get 40 pin Pre Soldered Header
- MicroSD Card (min 8 GB)
- E-Ink Display:
    - Pimoroni Inky Impression (7.3", 13.3")
    - Pimoroni Inky wHAT (4.2")
    - Waveshare e-Paper Displays (various displays, some are not supported though!)
- Micro USB Cable
**Optional Materials**
- Picture frame or 3D-printed stand

## Installation
To install InkyPi, follow these steps:

1. Clone the repository:
    ```bash
    git clone https://github.com/maessiglaessig/InkyPi.git
    ```
2. Navigate to the project directory:
    ```bash
    cd InkyPi
    ```
3. Run the installation script with sudo:
    ```bash
    sudo bash install/install.sh [-W <waveshare device model>]
    ``` 
     Option: 
    
    * -W \<waveshare device model\> - specify this parameter **ONLY** if installing for a Waveshare display.  After the -W option specify the Waveshare device model e.g. epd7in3f.

    e.g. for Inky displays use:
    ```bash
    sudo bash install/install.sh
    ```

    and for [Waveshare displays](#waveshare-display-support) use:
    ```bash
    sudo bash install/install.sh -W epd7in3f
    ```


After the installation is complete, the script will prompt you to reboot your Raspberry Pi. Once rebooted, the display will update to show the InkyPi splash screen.

Note: 
- The installation script requires sudo privileges to install and run the service. We recommend starting with a fresh installation of Raspberry Pi OS to avoid potential conflicts with existing software or configurations.
- The installation process will automatically enable the required SPI and I2C interfaces on your Raspberry Pi.

For more details, including instructions on how to image your microSD with Raspberry Pi OS, refer to [installation.md](./docs/installation.md). You can also checkout [this YouTube tutorial](https://youtu.be/L5PvQj1vfC4).

## Update
To update your InkyPi with the latest code changes, follow these steps:
1. Navigate to the project directory:
    ```bash
    cd InkyPi
    ```
2. Fetch the latest changes from the repository:
    ```bash
    git pull
    ```
3. Run the update script with sudo:
    ```bash
    sudo bash install/update.sh
    ```
This process ensures that any new updates, including code changes and additional dependencies, are properly applied without requiring a full reinstallation.

## Uninstall
To install InkyPi, simply run the following command:

```bash
sudo bash install/uninstall.sh
```

## Roadmap
...

## Waveshare Display Support

Waveshare offers a range of e-Paper displays, similar to the Inky screens from Pimoroni, but with slightly different requirements. While Inky displays auto-configure via the inky Python library, Waveshare displays require model-specific drivers from their [Python EPD library](https://github.com/waveshareteam/e-Paper/tree/master/RaspberryPi_JetsonNano/python/lib/waveshare_epd).

This project has been tested with several Waveshare models. **Displays based on the IT8951 controller are not supported**, and **screens smaller than 4 inches are not recommended** due to limited resolution.

If your display model has a corresponding driver in the link above, it’s likely to be compatible. When running the installation script, use the -W option to specify your display model (without the .py extension). The script will automatically fetch and install the correct driver.

## License

Distributed under the GPL 3.0 License, see [LICENSE](./LICENSE) for more information.

This project includes fonts and icons with separate licensing and attribution requirements. See [Attribution](./docs/attribution.md) for details.

## Issues

Check out the [troubleshooting guide](./docs/troubleshooting.md). If you're still having trouble, feel free to create an issue on the [GitHub Issues](https://github.com/maessiglaessig/InkyPi/issues) page.

If you're using a Pi Zero W, note that there are known issues during the installation process. See [Known Issues during Pi Zero W Installation](./docs/troubleshooting.md#known-issues-during-pi-zero-w-installation) section in the troubleshooting guide for additional details..

## Acknowledgements
Check out the base of my project:

- [InkyPi](https://github.com/fatihak/InkyPi)

Check out these similar projects:

- [PaperPi](https://github.com/txoof/PaperPi) - awesome project that supports waveshare devices
    - shoutout to @txoof for assisting with InkyPi's installation process
- [InkyCal](https://github.com/aceinnolab/Inkycal) - has modular plugins for building custom dashboards
- [PiInk](https://github.com/tlstommy/PiInk) - inspiration behind InkyPi's flask web ui
- [rpi_weather_display](https://github.com/sjnims/rpi_weather_display) - alternative eink weather dashboard with advanced power effiency
