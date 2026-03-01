# Test encoding fix
text = b'\xc3\xa2\xc2\x80\xc2\x98Apps\xc3\xa2\xc2\x80\xc2\x99'.decode('utf-8')
print('Input:', repr(text))

# Apply replacements  
text = text.replace('â\x80\x98', "'")
text = text.replace('â\x80\x99', "'")

print('Output:', repr(text))
