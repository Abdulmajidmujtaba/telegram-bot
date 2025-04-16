# Markdown Formatting Guide

This bot now supports rich text formatting using Telegram's MarkdownV2 format, which allows for more expressive and well-structured messages.

## How It Works

All messages sent by the bot use the telegramify-markdown library to convert Markdown into Telegram's MarkdownV2 format. This means you can write normal Markdown in your messages and it will be properly formatted when displayed in Telegram.

## Supported Markdown Features

The bot supports the following Markdown formatting:

### Text Styling

- **Bold**: `**bold text**` or `*bold text*`
- *Italic*: `_italic text_` 
- __Underline__: `__underlined text__`
- ~~Strikethrough~~: `~~strikethrough text~~`
- ||Spoiler||: `||spoiler text||`
- `Code`: `` `inline code` ``
- Combined styling: `**bold _italic_**`

### Headings

```
# Heading 1
## Heading 2
### Heading 3
#### Heading 4
##### Heading 5
###### Heading 6
```

### Lists

Unordered lists:
```
- Item 1
- Item 2
  - Subitem 2.1
  - Subitem 2.2
- Item 3
```

Ordered lists:
```
1. First item
2. Second item
3. Third item
```

Task lists:
```
- [ ] Uncompleted task
- [x] Completed task
```

### Links

`[link text](https://example.com)`

### Code Blocks

````
```
def hello_world():
    print("Hello, World!")
```
````

### Block Quotes

```
> This is a quote
> It can span multiple lines
```

### Tables

```
| Header 1 | Header 2 | Header 3 |
|----------|:--------:|---------:|
| Left     | Center   | Right    |
| aligned  | aligned  | aligned  |
```

### LaTeX Math

Inline LaTeX: `\(F = G\frac{m_1m_2}{r^2}\)`

Block LaTeX:
```
\[
F = G\frac{m_1m_2}{r^2}
\]
```

## For Developers

If you need to send custom Markdown messages in the bot, use the `send_markdown_message` method of the SummaryBot class:

```python
await bot.send_markdown_message(chat_id, text, context)
```

For simple text that doesn't need to be split into multiple messages, you can also use the `markdownify` function:

```python
from bot.utils.markdown_utils import markdownify

formatted_text = markdownify(text)
await context.bot.send_message(
    chat_id=chat_id,
    text=formatted_text,
    parse_mode="MarkdownV2"
)
```

For longer text that might need to be split into multiple messages, use the `telegramify` function:

```python
from bot.utils.markdown_utils import telegramify

chunks = telegramify(long_text)
for chunk in chunks:
    await context.bot.send_message(
        chat_id=chat_id,
        text=chunk,
        parse_mode="MarkdownV2"
    )
``` 