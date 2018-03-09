# inireader  
## A small script for reading from and writing to configuration files \(\.ini\)  
This script makes configuration files accessible from Python\.  
  
## Quick documentation  
### Example:  

    >>> from inireader import Config
    >>> cfg = Config("config.ini")
    >>> print(cfg["settings"]["language"])
    'EN'
    >>> cfg["settings", "language"] = 'ES'
    >>> print(cfg["settings", "language"])
    'ES'
    >>> cfg.save()
  
### Reference  

    Config(file_path[, comment_char, escape_char]) -> Config instance
  
This instance contains the entire configuration of the file at <**file_path**>\.  
<**comment_char**> can be set to the desired character used to indicate comments \(**';'** by default\)  
<**escape_char**> can be set to the desired escape character \(**'\\'** by default\)  

    Config[section][key] -> (closest matching type) <value>
  
Returns the <**value**> of <**key**> in <**section**>\.  

    Config[section, key] = value
  
Sets the <**value**> of <**key**> in <**section**>\.  

    Config.save() -> None
  
Saves the configuration\.  
