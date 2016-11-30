
install virtualenv python 3.5

install python packages:
```
pip install -r requirements.txt
```

enable jupyterlab:
```
jupyter serverextension enable --py jupyterlab --sys-prefix
```

start jupyterlab:
```
jupyter lab
```



usage:

```
>>> import kechain
```

```
>>> kechain.set_auth_token("################")
```

```
>>> kechain.sync()
Retrieved 14 parts
```    

```
>>> wheel = kechain.find_part('Front Wheel')
>>> mat = wheel.find_property('Rim Material')
>>> mat.value = 'Steel'
```

```
>>> kechain.find_part('Rear Wheel').find_property('Rim Material').value = 'Carbon'
```

```
>>> kechain.sync()
Updated 2 properties
```