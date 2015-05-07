# Creep

A Minecraft package manager for mods

## Prerequisites

 - Download Minecraft
 - Have valid Minecraft account
 - Download Minecraft Forge Installer from http://files.minecraftforge.net/maven/net/minecraftforge/forge/index_1.7.10.html
 - Run the Forge installer
 - Inside Minecraft, create or edit a profile where "Use Version:" is set to
   the forge version just installed

## Installation

 - Clone this repo
 - Symlink the `creep` file into your `$PATH`

## Usage

 - `creep list` - will list all the known packages (mods) in the repository
 - `creep install <package>` - will install the package to your `~/.minecraft/mods` folder
 - `creep uninstall <package>` - will remove the package from your mods folder

The mod files are stored in a cache directory in `~/.creep/cache`

## Future Plans

 - Support dependencies
 - Have a registry where people can define their mods

Example mod.json
```
{
  "name": "thefrogmc/better-furnaces",
  "version": "4.3",
  "description": "Adds some new furnaces to the game",
  "keywords": "iron furnace, gold furnace, diamond furnace, hell furnace, extreme furnace",
  "require": {
    "minecraft": "1.7.10",
    "forge": "*"
  },
  "filename": "[1.7.10]Better_Furnaces_V4.3.jar",
  "author": "TheFrogMC",
  "homepage": "http://www.minecraftforum.net/forums/mapping-and-modding/minecraft-mods/1279439-better-furnaces-mod"
}   
```

 - You can search the registry for mods by typing `creep search furnace`
 - You can install mods by typing `creep install better-furnaces`
 - You can uninstall mods by typing `creep uninstall better-furnaces`
 - You can make packages of mods by requiring other mods or packages

Another example mod.json
```
{
  "name": "flan/flansmod",
  "version": "4.10.0",
  "description": "Adds modern weaponry and vehicles to the game",
  "keywords": "guns, grenades, war, planes, cars, tanks",
  "require": {
    "minecraft": "1.7.10",
    "forge": "*"
  },
  "filename": "Flans Mod-1.7.10-4.10.0.jar",
  "homepage": "http://flansmod.com/"
}
```

```
{
  "name": "flan/simple-parts",
  "version": "4.10.0",
  "description": "This pack adds a ton of plane and vehicle parts for other content packs to use in their recipes",
  "keywords": "parts, simple, requirement",
  "require": {
    "minecraft": "1.7.10",
    "flan/flansmod": "4.10.0"
  },
  "filename": "Simple Parts-Content Pack-1.7.10-4.10.0.jar",
  "homepage": "http://flansmod.com/content-pack/2/",
  "installdir": "Flan"
}
```

An example content pack for flans mod:
```
{
  "name": "flan/modern-warfare",
  "version": "4.10.0",
  "description": "A vast selection of modern guns, from Desert Eagles and AK47s to P90s and RPGs, with armour and team presets thrown in, so you can turn Minecraft into a modern battlefield in a matter of moments",
  "keywords": "guns, modern",
  "require": {
    "flan/simple-parts": "4.10.0"
  },
  "filename": "Modern Warfare-Content Pack-1.7.10-4.10.0.jar",
  "homepage": "http://flansmod.com/content-pack/4/Modern_Weapons_Pack",
  "installdir": "Flan"
}
```

A repository file defines the list of available packages:
```
{
  "packages": {
    "thefrogmc/better-furnaces": {
      "4.3": {
        "name": "thefrogmc/better-furnaces",
        "version": "4.3",
        "description": "Adds some new furnaces to the game",
        "keywords": "iron furnace, gold furnace, diamond furnace, hell furnace, extreme furnace",
        "require": {
          "minecraft": "1.7.10",
          "forge": "*"
        },
        "filename": "[1.7.10]Better_Furnaces_V4.3.jar",
        "author": "TheFrogMC",
        "homepage": "http://www.minecraftforum.net/forums/mapping-and-modding/minecraft-mods/1279439-better-furnaces-mod"
      }
    },
    "copygirl/better-storage": {
      "0.13.1.126": {
        "name": "copygirl/better-storage",
        "version": "0.13.1.126",
        "description": "Offers more storage options",
        "keywords": "storage, chest, locks, keys, lockers",
        "require": {
          "minecraft": "1.7.10",
          "forge": ">=10.13.2.1230"
        },
        "url": "https://github.com/copygirl/BetterStorage/releases/download/v0.13.1.126/BetterStorage-1.7.10-0.13.1.126.jar",
        "author": "copygirl",
        "homepage": "https://github.com/copygirl/BetterStorage"
      }
    }
  }
}
```
