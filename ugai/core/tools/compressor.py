def compress_text(text,max_chars=12000):
 if len(text)<=max_chars:return text
 h=max_chars*2//3; return text[:h]+"\n...[compressed]...\n"+text[-(max_chars-h):]
