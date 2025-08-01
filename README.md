## 搜狗细胞词库（.scel）转换工具

### 简介

该项目参考 [scel2txt](https://github.com/lewang0/scel2txt) 和 [libscel](https://github.com/fkxxyz/libscel) ，在此表示感谢

### 用法

#### 直接输出至文本

```shell
scel2txt.py <input> <frequence>
```

输出格式为 "词语\t拼音\t词频"

参数详解:

- input    .scel文件路径，或含有.scel文件的文件夹
  （输出文件为同路径下的同名.txt文件）
- frequence    为本次转换指定统一词频，可缺省，默认为0

#### 当成库使用

从文件读取

```python
import scel
s = scel.scel()
s.load('网络流行新词【官方推荐】.scel')
print(s.title)
print(s.category)
print(s.description)
print(s.samples)
print("一共有 %d 个词汇" % len(s.word_list))
print("第一个词是 %s" % str(s.word_list[0]))
print("一共有 %d 个被删除的词汇" % len(s.del_words))
```
