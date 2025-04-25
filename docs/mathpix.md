# Mathpix API v3 Reference

[NAV [Image: No description](https://converturltomd.com/images/navbar-cad8cdcb.png)](#) 

[[Image: No description](https://converturltomd.com/images/logo-13037355.png)](https://mathpix.com/)

[cURL](#) [Python](#)

*   [Introduction](#introduction)
*   [Authorization](#authorization)
    *   [Using server side API keys](#using-server-side-api-keys)
    *   [Using client side app tokens](#using-client-side-app-tokens)
*   [Process an image](#process-an-image)
    *   [Request parameters](#request-parameters)
    *   [Format descriptions](#format-descriptions)
    *   [DataOptions object](#dataoptions-object)
    *   [Response body](#response-body)
    *   [Data object](#data-object)
    *   [DetectedAlphabet object](#detectedalphabet-object)
    *   [AlphabetsAllowed object](#alphabetsallowed-object)
    *   [LineData object](#linedata-object)
    *   [WordData object](#worddata-object)
    *   [Auto rotation](#auto-rotation)
*   [Process stroke data](#process-stroke-data)
    *   [Request parameters](#request-parameters-2)
    *   [Response body](#response-body-2)
*   [Process an equation image](#process-an-equation-image)
    *   [Request parameters](#request-parameters-3)
    *   [Formatting](#formatting)
    *   [Format options](#format-options)
    *   [Response body](#response-body-3)
    *   [Image properties](#image-properties)
*   [Query image results](#query-image-results)
    *   [Request parameters](#request-parameters-4)
    *   [Result object](#result-object)
*   [Query ocr usage](#query-ocr-usage)
    *   [Request parameters](#request-parameters-5)
    *   [Response body](#response-body-4)
*   [Process a PDF](#process-a-pdf)
    *   [Request parameters for uploading PDFs](#request-parameters-for-uploading-pdfs)
    *   [Response body](#response-body-5)
    *   [Stream PDF pages](#stream-pdf-pages)
    *   [Processing status](#processing-status)
    *   [Get conversion status](#get-conversion-status)
    *   [Conversion results](#conversion-results)
    *   [PDF lines data](#pdf-lines-data)
    *   [PDF MMD lines data](#pdf-mmd-lines-data)
    *   [Deleting PDF results](#deleting-pdf-results)
*   [Convert Documents](#convert-documents)
    *   [Request parameters](#request-parameters-6)
    *   [Response body](#response-body-6)
    *   [Conversion Formats](#conversion-formats)
    *   [Conversion Options](#conversion-options)
    *   [Get conversion status](#get-conversion-status-2)
    *   [Conversion results](#conversion-results-2)
*   [Query PDF results](#query-pdf-results)
    *   [Request parameters](#request-parameters-7)
    *   [Query result object](#query-result-object)
*   [Process a batch](#process-a-batch)
    *   [Process images as a batch with `v3/text` behavior](#process-images-as-a-batch-with-v3-text-behavior)
*   [Callback object](#callback-object)
*   [Supported image types](#supported-image-types)
*   [Error handling](#error-handling)
    *   [Error info object](#error-info-object)
    *   [Error id strings](#error-id-strings)
*   [Privacy](#privacy)
*   [Long division](#long-division)
*   [Latency considerations](#latency-considerations)
*   [Supported math commands](#supported-math-commands)
*   [System status](#system-status)

*   [Sign Up for a Developer Key](https://console.mathpix.com)
*   [Check out some examples!](https://mathpix.com/docs/ocr/examples)

# Introduction

```
git clone [email protected]:Mathpix/api-examples.git
cd api-examples/images
```

MathpixOCR recognizes printed and handwritten STEM document content, including math, text, tables, and chemistry diagrams, from an image, stroke data, or a PDF file. The returned content for an image or stroke data may be [Mathpix Markdown](https://mathpix.com/docs/mathpix-markdown/overview), LaTeX, AsciiMath, MathML, or HTML. For a PDF file the content is also available as docx.

This page describes the MathpixOCR requests and responses. If you have any questions or problems, please send email to [\[email protected\]](/cdn-cgi/l/email-protection).

# Authorization

## Using server side API keys

> Include the following headers in every request:

```
{
  "app_id": "APP_ID",
  "app_key": "APP_KEY"
}
```

Every MathpixOCR server side request should include two headers: `app_id` to identify your application and `app_key` to authorize access to the service. You can find your API key on your organization page at [https://console.mathpix.com](https://console.mathpix.com).

Note: never include your API keys inside client side code. Such API keys can easily be stolen by hackers by inspecting the app binary. If you want to make direct requests from client side code to the API, use app tokens, described below.

## Using client side app tokens

> To get a temporary `app_token`, do the following:

```
curl -X POST https://api.mathpix.com/v3/app-tokens -H 'app_key: APP_KEY'
```

```
import requests

url = "https://api.mathpix.com/v3/app-tokens"
headers = {
    "app_key": "APP_KEY"
}

response = requests.post(url, headers=headers)

print(response.json())
```

> This then returns an `app_token` value which can be used as an `app_token` header to authenticate requests:

```
{
  "app_token": "token_e06840c31fbfd28c2aba38207e417c4e",
  "app_token_expires_at": "1649699265744"
}
```

You can also create short lived client side tokens to make requests from clients (for example mobile apps) directly to Mathpix OCR servers. This reduces the need for customers to proxy their requests through their server to secure the requests. As such, it avoids an additional network hop, resulting in improved latency.

To get a temporary app token on your server to hand off to a client, use your API key to make a request to:

**POST api.mathpix.com/v3/app-tokens**

The `app_token` will last for 5 minutes, after which requests will return HTTP status 401 (unauthorized). In such cases, the client can request an additional app token. Requests to create app tokens are free of charge.

With `app_token`, you only need a single authenticated route on your servers to get an `app_token` for your user. This means you do not need to worry about proxying image requests to our servers.

We have designed app tokens for individual image and digital ink requests (strokes) only. As such, app tokens have the following limitations when compared to API keys:

*   cannot access PDF functionality
*   cannot access historical data
*   cannot access account admin data
*   cannot not make batch / async requests

Note: the app tokens feature is in beta and is being actively developed.

Request JSON parameters:

Parameter

Type

Description

include\_strokes\_session\_id (optional)

boolean

Return a `strokes_session_id` value that can be used for live update drawing, see [v3/strokes](#process-stroke-data) for more info

expires (optional)

number (seconds)

Specifies how long the `app_token` will last. The Default is 300 seconds. Values can range from 30 - 43200 seconds (12 hours) for an `app_token` and from 30 - 300 seconds (5 minutes) for a request with `include_strokes_session_id`

Response JSON parameters:

Parameter

Type

Description

app\_token

string

App token to be used in headers of v3/text, v3/latex, or v3/strokes requests

strokes\_session\_id (optional)

string

if requested via, `include_strokes_session_id`, you can use this value to take advantage of our live digital ink pricing and SDKs, see [v3/strokes](#process-stroke-data)

app\_token\_expires\_at

number (seconds)

Specifies when the `app_token` will expire in Unix time

# Process an image

> Example image:
> 
> [Image: picture](https://mathpix-ocr-examples.s3.amazonaws.com/cases_hw.jpg)
> 
> JSON request body to send an image URL:

```
{
  "src": "https://mathpix-ocr-examples.s3.amazonaws.com/cases_hw.jpg",
  "formats": ["text", "data"],
  "data_options": {
    "include_asciimath": true
  }
}
```

> Response:

```
{
  "auto_rotate_confidence": 0,
  "auto_rotate_degrees": 0,
  "confidence": 1,
  "confidence_rate": 1,
  "data": [
    {
      "type": "asciimath",
      "value": "f(x)={[x^(2),\" if \"x < 0],[2x,\" if \"x >= 0]:}"
    }
  ],
  "image_height": 332,
  "image_width": 850,
  "is_handwritten": true,
  "is_printed": false,
  "latex_styled": "f(x)=\\left\\{\\begin{array}{ll}\nx^{2} & \\text { if } x<0 \\\\\n2 x & \\text { if } x \\geq 0\n\\end{array}\\right.",
  "request_id": "2025_04_16_d884f78c7c80ba983343g",
  "text": "\\( f(x)=\\left\\{\\begin{array}{ll}x^{2} & \\text { if } x<0 \\\\ 2 x & \\text { if } x \\geq 0\\end{array}\\right. \\)",
  "version": "SuperNet-100"
}
```

**POST api.mathpix.com/v3/text**

To process an image with MathpixOCR, a client may post a form to v3/text containing the image file and a single form field `options_json` specifying the desired options. Alternatively, a client may post a JSON body to v3/text containing a link to the image in the `src` field along with the desired options. For backward compatibility a client also may post a JSON body containing the base64 encoding of the image in the `src` field.

The response body is JSON containing the recognized content and information about the recognition. The `text` field contains Mathpix Markdown, including math as LaTeX inside inline delimiters `\( ... \)` and block mode delimiters `\[ .... \]`. Chemistry diagrams are returned as `<smiles>...</smiles>` where `...` is the SMILES (simplified molecular-input line-entry system) representation of chemistry diagrams. Lines are separated with `\n` newline characters. In some cases (e.g., multiple choice equations) horizontally-aligned content will be flattened into different lines.

We also provide structured data results via the `data` and `html` options. The `data` output returns a list of extracted formats (such as `tsv` for tables, or `asciimath` for equations). The `html` output provides annotated HTML compatible with HTML/XML parsers.

## Request parameters

> Example of sending an image URL:

```
#!/usr/bin/env python
import requests
import json

r = requests.post("https://api.mathpix.com/v3/text",
        json={
            "src": "https://mathpix-ocr-examples.s3.amazonaws.com/cases_hw.jpg",
            "math_inline_delimiters": ["$", "$"],
            "rm_spaces": True
        },
        headers={
            "app_id": "APP_ID",
            "app_key": "APP_KEY",
            "Content-type": "application/json"
        }
    )
print(json.dumps(r.json(), indent=4, sort_keys=True))
```

```
curl -X POST https://api.mathpix.com/v3/text \
-H 'app_id: APP_ID' \
-H 'app_key: APP_KEY' \
-H 'Content-Type: application/json' \
--data '{"src": "https://mathpix-ocr-examples.s3.amazonaws.com/cases_hw.jpg", "math_inline_delimiters": ["$", "$"], "rm_spaces": true}'
```

> Send an image file:

```
#!/usr/bin/env python
import requests
import json

r = requests.post("https://api.mathpix.com/v3/text",
    files={"file": open("cases_hw.jpg","rb")},
    data={
      "options_json": json.dumps({
        "math_inline_delimiters": ["$", "$"],
        "rm_spaces": True
      })
    },
    headers={
        "app_id": "APP_ID",
        "app_key": "APP_KEY"
    }
)
print(json.dumps(r.json(), indent=4, sort_keys=True))
```

```
curl -X POST https://api.mathpix.com/v3/text \
-H 'app_id: APP_ID' \
-H 'app_key: APP_KEY' \
--form 'file=@"cases_hw.jpg"' \
--form 'options_json="{\"math_inline_delimiters\": [\"$\", \"$\"], \"rm_spaces\": true}"'
```

> Response:

```
{
  "auto_rotate_confidence": 0,
  "auto_rotate_degrees": 0,
  "confidence": 1,
  "confidence_rate": 1,
  "image_height": 332,
  "image_width": 850,
  "is_handwritten": true,
  "is_printed": false,
  "latex_styled": "f(x)=\\left\\{\\begin{array}{ll}\nx^{2} & \\text { if } x<0 \\\\\n2 x & \\text { if } x \\geq 0\n\\end{array}\\right.",
  "request_id": "2025_04_16_14b535679f6c84954b3dg",
  "text": "$f(x)=\\left\\{\\begin{array}{ll}x^{2} & \\text { if } x<0 \\\\ 2 x & \\text { if } x \\geq 0\\end{array}\\right.$",
  "version": "SuperNet-100"
}
```

```
{
  "src": "https://mathpix-ocr-examples.s3.amazonaws.com/cases_hw.jpg",
  "formats": ["text", "data", "html"],
  "data_options": {
    "include_asciimath": true,
    "include_latex": true
  }
}
```

Parameter

Type

Description

src (optional)

string

Image URL

metadata (optional)

object

Key-value object

tags (optional)

\[string\]

Tags are lists of strings that can be used to identify results. see [query image results](#query-image-results)

async (optional)

\[bool\]

This flag is to be used when sending non-interactive requests

callback (optional)

object

[Callback object](#callback-object)

formats (optional)

\[string\]

List of formats, one of `text`, `data`, `html`, `latex_styled`, see [Format Descriptions](#format-descriptions)

data\_options (optional)

object

See [DataOptions](#dataoptions-object) section, specifies outputs for `data` and `html` return fields

include\_detected\_alphabets (optional)

bool

Return detected alphabets

alphabets\_allowed (optional)

object

See [AlphabetsAllowed](#alphabetsallowed-object) section, use this to specify which alphabets you don't want in the output

region (optional)

object

Specify the image area with the pixel coordinates `top_left_x`, `top_left_y`, `width`, and `height`

enable\_blue\_hsv\_filter (optional)

bool

Enables a special mode of image processing where it OCRs blue hue text exclusively, default false.

confidence\_threshold (optional)

number in \[0,1\]

Specifies threshold for triggering confidence errors

confidence\_rate\_threshold (optional)

number in \[0,1\]

Specifies threshold for triggering confidence errors, default 0.75 (symbol level threshold)

include\_equation\_tags (optional)

bool

Specifies whether to include equation number tags inside equations LaTeX in the form of `\tag{eq_number}`, where `eq_number` is an equation number (e.g. `1.12`). When set to `true`, it sets `"idiomatic_eqn_arrays": true`, because equation numbering works better in those environments compared to the _array_ environment.

include\_line\_data (optional)

bool

Specifies whether to return information segmented line by line, see [LineData object](#linedata-object) section for details

include\_word\_data (optional)

bool

Specifies whether to return information segmented word by word, see [WordData object](#worddata-object) section for details

include\_smiles (optional)

bool

Enable experimental chemistry diagram OCR, via RDKIT normalized SMILES with `isomericSmiles=False`, included in `text` output format, via MMD SMILES syntax `<smiles>...</smiles>`

include\_inchi (optional)

bool

Include InChI data as XML attributes inside `<smiles>` elements, for examples `<smiles inchi="..." inchikey="...">...</smiles>`; only applies when `include_smiles` is true

include\_geometry\_data (optional)

bool

Enable data extraction for geometry diagrams (currently only supports triangle diagrams); see [GeometryData](#geometrydata-object)

include\_diagram\_text (optional)

bool

Enables text extraction from diagrams, `false` by default (use with `"include_line_data": true`). The extracted text will be part of line data, and not part of the `text`, or any other output format specified. The `parent_id` of these text lines will correspond to the `id` of one of the diagrams in the line data. Also, diagram will have `children_ids` to store references to these text lines.

auto\_rotate\_confidence\_threshold (optional)

number in \[0,1\]

Specifies threshold for auto rotating image to correct orientation; by default it is set to 0.99, can be disabled with a value of 1 (see [Auto rotation](#auto-rotation) section for details)

rm\_spaces (optional)

bool

Determines whether extra white space is removed from equations in `latex_styled` and `text` formats. Default is `true`.

rm\_fonts (optional)

bool

Determines whether font commands such as \\mathbf and \\mathrm are removed from equations in `latex_styled` and `text` formats. Default is `false`.

idiomatic\_eqn\_arrays (optional)

bool

Specifies whether to use aligned, gathered, or cases instead of an array environment for a list of equations. Default is `false`.

idiomatic\_braces (optional)

bool

Specifies whether to remove unnecessary braces for LaTeX output. When true, `x^2` is returned instead of `x^{2}`. Default is `false`.

numbers\_default\_to\_math (optional)

bool

Specifies whether numbers are always math, e.g., `Answer: \( 17 \)` instead of `Answer: 17`. Default is `false`.

math\_fonts\_default\_to\_math (optional)

bool

Specifies whether math fonts are always math, e.g., `Answer: \( 2 \mathrm { ms } \)` instead of `Answer: 2 ms`. Default is `false`.

math\_inline\_delimiters (optional)

\[string, string\]

Specifies begin inline math and end inline math delimiters for `text` outputs. Default is `["\\(", "\\)"]`.

math\_display\_delimiters (optional)

\[string, string\]

Specifies begin display math and end display math delimiters for `text` outputs. Default is `["\\[", "\\]"]`.

enable\_spell\_check

bool

Enables a predictive mode for English handwriting that takes word frequencies into account; this option is skipped when the language is not detected as English; incorrectly spelled words that are clearly written will not be changed, this predictive mode is only enabled when the underlying word is visually ambiguous, see [here](https://mathpix.com/docs/ocr/examples#handwritten-text-with-spellcheck) for an example.

enable\_tables\_fallback

bool

Enables advanced table processing algorithm that supports very large and complex tables. Defaults to `false`

fullwidth\_punctuation (optional)

bool

Controls if punctuation will be fullwidth Unicode (default for east Asian languages like Chines), of halfwidth Unicode (default for Latin scripts, Cyrillic scripts etc.). Default value is `null`, which means fullwidth vs halfwidth will be decided based on image content. Punctuation inside math will always stay halfwidth.

## Format descriptions

MathpixOCR returns strings in one of the selected formats:

Format

Description

text

Mathpix Markdown

html

HTML rendered from `text` via mathpix-markdown-it

data

Data computed from `text` as specified in the `data_options` request parameter

latex\_styled

Styled Latex, returned only in cases that the whole image can be reduced to a single equation

## DataOptions object

Data options are used to return elements of the image output. These outputs are all computed from the `text` format described above.

Key

Type

Description

include\_svg (optional)

bool

include math SVG in `html` and `data` formats

include\_table\_html (optional)

bool

include HTML for `html` and `data` outputs (tables only)

include\_latex (optional)

bool

include math mode latex in `data` and `html`

include\_tsv (optional)

bool

include tab separated values (TSV) in `data` and `html` outputs (tables only)

include\_asciimath (optional)

bool

include asciimath in `data` and `html` outputs

include\_mathml (optional)

bool

include mathml in `data` and `html` outputs

## Response body

Field

Type

Description

request\_id

string

Request ID, for debugging purposes

text (optional)

string

Recognized `text` format, if such is found

latex\_styled (optional)

string

Math Latex string of math equation, if the image is of a single equation

confidence (optional)

number in \[0,1\]

Estimated probability 100% correct

confidence\_rate (optional)

number in \[0,1\]

Estimated confidence of output quality

line\_data (optional)

\[object\]

List of [LineData](#linedata-object) objects

word\_data (optional)

\[object\]

List of [WordData](#worddata-object) objects

data (optional)

\[object\]

List of [Data](#data-object) objects

html (optional)

string

Annotated HTML output

detected\_alphabets (optional)

\[object\]

[DetectedAlphabet](#detectedalphabet-object) object

is\_printed (optional)

bool

Specifies if printed content was detected in an image

is\_handwritten (optional)

bool

Specifies if handwritten content was detected in an image

auto\_rotate\_confidence (optional)

number in \[0,1\]

Estimated probability that image needs to be rotated, see [Auto rotation](#auto-rotation)

geometry\_data (optional)

\[object\]

List of [GeometryData](#geometrydata-object) objects

auto\_rotate\_degrees (optional)

number in {0, 90, -90, 180}

Estimated angle of rotation in degrees to put image in correct orientation, see [Auto rotation](#auto-rotation)

error (optional)

string

US locale error message

error\_info (optional)

object

Error info object

version

string

This string is opaque to clients and only useful as a way of understanding differences in results for requests using the same image. Our service relies on training data, the service implementation, and the underlying platforms we run on (e.g., AWS, PyTorch). Initially, the version string will only change when the training data or process changes, but in the future we might provide additional distinctions between versions.

## Data object

Data objects allow extracting the math elements from an OCR result.

Field

Type

Description

type

string

one of `asciimath`, `mathml`, `latex`, `svg`, `tsv`

value

string

value corresponding to `type`

## DetectedAlphabet object

The detected\_alphabets object in a result contains a field that is true of false for each known alphabet. The field is true if any characters from the alphabet are recognized in the image, regardless of whether any of the result fields contain the characters.

Field

Type

Description

en

bool

English

hi

bool

Hindi Devanagari

zh

bool

Chinese

ja

bool

Kana Hiragana or Katakana

ko

bool

Hangul Jamo

ru

bool

Russian

th

bool

Thai

ta

bool

Tamil

te

bool

Telugu

gu

bool

Gujarati

bn

bool

Bengali

vi

bool

Vietnamese

## AlphabetsAllowed object

```
{
  "formats": ["text"],
  "alphabets_allowed": {
    "hi": false,
    "zh": false,
    "ja": false,
    "ko": false,
    "ru": false,
    "th": false,
    "ta": false,
    "te": false,
    "gu": false,
    "bn": false,
    "vi": false
  }
}
```

There are cases where it is not easy to infer the correct alphabet for a single letter because there are different letters from different alphabets that look alike. To illustrate, one example is conflict between Latin `B` and Cyrillic `В` (that is Latin `V`). While being displayed almost the same, they essentially have different Unicode encodings. The option `alphabets_allowed` can be used to specify map from string to boolean values which can be used to prevent symbols from unwanted alphabet appearing in the result. Map keys that are valid correspond to the values in `Field` column of the table specified in `Detected alphabet object` section (e.g. `hi` or `ru`). By default all alphabets are allowed in the output, to disable alphabet specify `"alphabets_allowed": {"alphabet_key": false}`.

Specifying `"alphabets_allowed": {"alphabet_key": true}` has the same effect as not specifying that alphabet inside `alphabets_allowed` map.

## LineData object

> [Image: picture](https://mathpix.com/examples/text_with_diagram.png)
> 
> Example request:

```
{
  "src": "https://mathpix.com/examples/text_with_diagram.png",
  "formats": ["text"],
  "include_line_data": true
}
```

> JSON response:

```
{
  "auto_rotate_confidence": 0,
  "auto_rotate_degrees": 0,
  "confidence": 0.45044320869814447,
  "confidence_rate": 0.9904373020612357,
  "image_height": 733,
  "image_width": 932,
  "is_handwritten": false,
  "is_printed": true,
  "latex_styled": "\\text { Equivalent resistance between points } \\mathrm{A} \\& \\mathrm{~B} \\text { in the adjacent circuit is - }",
  "line_data": [
    {
      "after_hyphen": false,
      "cnt": [[62,37],[265,39],[542,45],[787,54],[860,56],[863,71],[863,85],[860,93],[784,93],[451,87],[87,76],[31,73],[0,71],[0,37]],
      "confidence": 0.45044320869814447,
      "confidence_rate": 0.9904373020612357,
      "conversion_output": true,
      "id": "74d60966b4ad49a7acf63d2c7e6cbbc6",
      "included": true,
      "is_handwritten": false,
      "is_printed": true,
      "text": "Equivalent resistance between points \\( \\mathrm{A} \\& \\mathrm{~B} \\) in the adjacent circuit is -",
      "type": "text"
    },
    {
      "cnt": [[0,687],[0,238],[656,238],[656,687]],
      "conversion_output": false,
      "error_id": "image_not_supported",
      "id": "282982c526304333b76ba533d21dd909",
      "included": false,
      "is_handwritten": false,
      "is_printed": true,
      "type": "diagram"
    }
  ],
  "request_id": "2025_04_16_53b99d5828d61ab3e606g",
  "text": "Equivalent resistance between points \\( \\mathrm{A} \\& \\mathrm{~B} \\) in the adjacent circuit is -",
  "version": "SuperNet-100"
}
```

Field

Type

Description

id

string

Unique line identifier

parent\_id (optional)

string

Unique line identifier of the parent.

children\_ids (optional)

\[string\]

List of children unique identifiers.

type

string

See [line types and subtypes](#line-data-types-and-subtypes) for details.

subtype (optional)

string

See [line types and subtypes](#line-data-types-and-subtypes) for details.

cnt

\[\[x,y\]\]

Contour for line expressed as list of (x,y) pixel coordinate pairs

included

bool

Whether this line is included in the top level OCR result (deprecated, use `conversion_output`)

conversion\_output

boolean

Whether this line is included in the top level OCR result

is\_printed

bool

True if line has printed text, false otherwise.

is\_handwritten

bool

True if line has handwritten text, false otherwise.

error\_id (optional)

string

Error ID, reason why the line is not included in final result

text (optional)

string

Text (Mathpix Markdown) for line

confidence (optional)

number in \[0,1\]

Estimated probability 100% correct

confidence\_rate (optional)

number in \[0,1\]

Estimated confidence of output quality

after\_hyphen (optional)

bool

specifies if the current line occurs after the text line which ended with hyphen

html (optional)

string

Annotated HTML output for the line

data (optional)

\[Data\]

List of [Data](#data-object) object's

Specifying `include_line_data` to be true will add a `line_data` field to the response body. This field is a list of LineData objects that contain information about all textual line elements detected in the image. Simply concatenating information from the response's `line_data` is enough to recreate the top level `text`, `html`, and `data` fields in the response body.

The OCR engine does not support some lines, like diagrams, and these lines are therefore simply skipped. Some lines contain content that is most likely extraneous, like equation numbers. Additionally, sometimes the OCR engine simply cannot recognize the line with proper confidence. In all those cases `included` field is set to `false`, meaning the line is not part of the final result.

A line can have the following values for `error_id`:

*   image\_not\_supported - OCR engine doesn't accept this type of line
*   image\_max\_size - line is larger than maximal size which OCR engine supports
*   math\_confidence - OCR engine failed to confidently recognize the content of the line
*   image\_no\_content - line has strange spatial dimensions, e.g. height of the line is zero; this error is very unlikely to happen

### Line data types and subtypes

Here is a JSON listing of types and subtypes that might be returned as a part of [line data](#linedata-object), and also [PDF lines data](#pdf-lines-data) (types are the keys, and subtypes are given in a value list):

```
{
  "chart_info": [],
  "x_axis_tick_label": [],
  "y_axis_tick_label": [],
  "x_axis_label": [],
  "y_axis_label": [],
  "legend_label": [],
  "model_label": [],
  "page_info": [],
  "equation_number": [],
  "table": [],
  "diagram": [
    "algorithm",
    "pseudocode",
    "chemistry",
    "chemistry_reaction",
    "triangle"
  ],
  "chart": [
    "column",
    "bar",
    "line",
    "analytical",
    "pie",
    "scatter",
    "area"
  ],
  "diagram_info": [],
  "text": [
    "vertical",
    "big_capital_letter"
  ],
  "math": [],
  "column": [],
  "code": [],
  "pseudocode": [],
  "form_field": [
    "parentheses",
    "dotted",
    "dashed",
    "box",
    "checkbox",
    "circle"
  ],
  "multiple_choice_block": [],
  "multiple_choice_option": [],
  "footnote": [],
  "table_of_contents_container": [],
  "table_of_contents_row": [],
  "table_of_contents_item": [],
  "table_of_contents_number": [],
  "title": [],
  "quote": [],
  "section_header": [],
  "authors": [],
  "abstract": [],
  "rotated_container": [],
  "table_cell": [
    "split", 
    "spanning"
  ]
}
```

## WordData object

> Example request:
> 
> [Image: No description](https://mathpix.com/examples/text_with_math_0.jpg)

```
{
  "src": "https://mathpix.com/examples/text_with_math_0.jpg",
  "include_word_data": true
}
```

> JSON response:

```
{
  "is_printed": true,
  "is_handwritten": false,
  "auto_rotate_confidence": 0.00939574267408716,
  "auto_rotate_degrees": 0,
  "word_data": [
    {
      "type": "text",
      "cnt": [
        [111, 104],
        [3, 104],
        [3, 74],
        [111, 74]
      ],
      "text": "Perform",
      "confidence": 0.99951171875,
      "confidence_rate": 0.9999593007867263,
      "latex": "\\text { Perform }"
    },
    {
      "type": "text",
      "cnt": [
        [160, 104],
        [115, 104],
        [115, 74],
        [160, 74]
      ],
      "text": "the",
      "confidence": 1,
      "confidence_rate": 1,
      "latex": "\\text { the }"
    },
    {
      "type": "text",
      "cnt": [
        [286, 104],
        [163, 104],
        [163, 74],
        [286, 74]
      ],
      "text": "indicated",
      "confidence": 0.9970722198486328,
      "confidence_rate": 0.9997905880380586,
      "latex": "\\text { indicated }"
    },
    {
      "type": "text",
      "cnt": [
        [413, 107],
        [290, 107],
        [290, 77],
        [413, 77]
      ],
      "text": "operation",
      "confidence": 0.9985356330871582,
      "confidence_rate": 0.9998953311820248,
      "latex": "\\text { operation }"
    },
    {
      "type": "text",
      "cnt": [
        [469, 104],
        [417, 104],
        [417, 74],
        [469, 74]
      ],
      "text": "and",
      "confidence": 1,
      "confidence_rate": 1,
      "latex": "\\text { and }"
    },
    {
      "type": "text",
      "cnt": [
        [592, 108],
        [472, 108],
        [472, 74],
        [592, 74]
      ],
      "text": "simplify.",
      "confidence": 0.9790234565734863,
      "confidence_rate": 0.9984868832735626,
      "latex": "\\text { simplify. }"
    },
    {
      "type": "text",
      "cnt": [
        [126, 162],
        [100, 162],
        [100, 130],
        [126, 130]
      ],
      "text": "3)",
      "confidence": 0.998046875,
      "confidence_rate": 0.9997207483071853,
      "latex": "\\text { 3) }"
    },
    {
      "type": "math",
      "cnt": [
        [322, 191],
        [132, 191],
        [132, 110],
        [322, 110]
      ],
      "text": "\\( \\frac{2 p-2}{p} \\div \\frac{4 p-4}{9 p^{2}} \\)",
      "confidence": 0.99853515625,
      "confidence_rate": 0.9999436201400773,
      "latex": "\\frac{2 p-2}{p} \\div \\frac{4 p-4}{9 p^{2}}"
    }
  ]
}
```

Field

Type

Description

type

string

One of `text`, `math`, `table`, `diagram`, `equation_number`

subtype (optional)

string

Either not set, or `chemistry`, or `triangle` (more diagram subtypes coming soon)

cnt

\[\[x,y\]\]

Contour for word expressed as list of (x,y) pixel coordinate pairs

text (optional)

string

Text (Mathpix Markdown) for word

latex (optional)

string

Math mode LaTeX (Mathpix Markdown) for word

confidence (optional)

number in \[0,1\]

Estimated probability 100% correct

confidence\_rate (optional)

number in \[0,1\]

Estimated confidence of output quality

Specifying true for `include_word_data` will add a `word_data` field to the response body. This field is a a list of WordData objects containing information about all word level elements detected in the image.

## Auto rotation

Sometimes images that are received are in wrong orientation,one example of such image would look like this:

[Image: picture](https://mathpix.com/examples/algebra_rotated.jpg)

The goal of automatic rotation is to pick correct orientation for received images before any processing is done. The result of auto rotation looks like: [Image: picture](https://mathpix.com/examples/algebra.jpg)

One can control how confident our algorithm needs to be to perform auto rotation with request parameter `auto_rotate_confidence_threshold`, a number in \[0,1\]. By default the value 0.99 is used, which essentially means that algorithm will auto rotate image if it is 99% confident in that decision. Auto rotation can be disabled by specifying `"auto_rotate_confidence_threshold": 1` as a part of request being sent.

The response body will include two related fields:

*   `auto_rotate_confidence` - confidence of the algorithm in decision that image needs to be rotated, number in \[0,1\] which should be ~0 if image is in correct orientation and ~1 if image should be rotated; monitoring this value on custom workloads can be helpful in determining proper `auto_rotate_confidence_threshold` to be used with such workloads
*   `auto_rotate_degrees` - angle in degrees specifying how much to rotate original image to get image in proper orientation, number in {0, 90, -90, 180}, value 0 means image is already in correct orientation; this information can be used to put image in right orientation for other parts of image processing

# Process stroke data

**POST api.mathpix.com/v3/strokes**

To process strokes coordinates, a client may post a JSON body to v3/strokes containing the strokes data along with the same options available when processing an image.

This endpoint is very convenient for users that were generating images of handwritten math and text and then using the service v3/text, since with v3/strokes no image generation is required, the request payload is smaller and therefore it results in faster response time.

The LaTeX of the recognized handwriting is returned inside inline delimiters `\( ... \)` and block mode delimiters `\[ .... \]`. Lines are separated with `\n` newline characters. In some cases (e.g. multiple choice equations) we will try to flatten horizontally aligned content into different lines in order to keep the markup simple.

## Request parameters

> Send some strokes:

```
{
  "strokes": {
    "strokes": {
      "x": [
        [
          131, 131, 130, 130, 131, 133, 136, 146, 151, 158, 161, 162, 162, 162,
          162, 159, 155, 147, 142, 137, 136, 138, 143, 160, 171, 190, 197, 202,
          202, 202, 201, 194, 189, 177, 170, 158, 153, 150, 148
        ],
        [231, 231, 233, 235, 239, 248, 252, 260, 264, 273, 277, 280, 282, 283],
        [
          273, 272, 271, 270, 267, 262, 257, 249, 243, 240, 237, 235, 234, 234,
          233, 233
        ],
        [
          296, 296, 297, 299, 300, 301, 301, 302, 303, 304, 305, 306, 306, 305,
          304, 298, 294, 286, 283, 281, 281, 282, 284, 284, 285, 287, 290, 293,
          294, 299, 301, 308, 309, 314, 315, 316
        ]
      ],
      "y": [
        [
          213, 213, 212, 211, 210, 208, 207, 206, 206, 209, 212, 217, 220, 227,
          230, 234, 236, 238, 239, 239, 239, 239, 239, 239, 241, 247, 252, 259,
          261, 264, 266, 269, 270, 271, 271, 271, 270, 269, 268
        ],
        [231, 231, 232, 235, 238, 246, 249, 257, 261, 267, 270, 272, 273, 274],
        [
          230, 230, 230, 231, 234, 240, 246, 258, 268, 273, 277, 281, 281, 283,
          283, 284
        ],
        [
          192, 192, 191, 189, 188, 187, 187, 187, 188, 188, 190, 193, 195, 198,
          200, 205, 208, 213, 215, 215, 215, 214, 214, 214, 214, 216, 218, 220,
          221, 223, 223, 223, 223, 221, 221, 220
        ]
      ]
    }
  }
}
```

```
#!/usr/bin/env python
import requests
import json

# put input strokes here
strokes_string = '{"strokes": {\
    "x": [[131,131,130,130,131,133,136,146,151,158,161,162,162,162,162,159,155,147,142,137,136,138,143,160,171,190,197,202,202,202,201,194,189,177,170,158,153,150,148],[231,231,233,235,239,248,252,260,264,273,277,280,282,283],[273,272,271,270,267,262,257,249,243,240,237,235,234,234,233,233],[296,296,297,299,300,301,301,302,303,304,305,306,306,305,304,298,294,286,283,281,281,282,284,284,285,287,290,293,294,299,301,308,309,314,315,316]],\
    "y": [[213,213,212,211,210,208,207,206,206,209,212,217,220,227,230,234,236,238,239,239,239,239,239,239,241,247,252,259,261,264,266,269,270,271,271,271,270,269,268],[231,231,232,235,238,246,249,257,261,267,270,272,273,274],[230,230,230,231,234,240,246,258,268,273,277,281,281,283,283,284],[192,192,191,189,188,187,187,187,188,188,190,193,195,198,200,205,208,213,215,215,215,214,214,214,214,216,218,220,221,223,223,223,223,221,221,220]]\
  }}'
strokes = json.loads(strokes_string)
r = requests.post("https://api.mathpix.com/v3/strokes",
    json={"strokes": strokes},
    headers={"app_id": "APP_ID", "app_key": "APP_KEY",
             "Content-type": "application/json"})
print(json.dumps(r.json(), indent=4, sort_keys=True))
```

```
curl -X POST https://api.mathpix.com/v3/strokes \
-H 'app_id: APP_ID' \
-H 'app_key: APP_KEY' \
-H 'Content-Type: application/json' \
--data '{ "strokes": {"strokes": {
  "x": [[131,131,130,130,131,133,136,146,151,158,161,162,162,162,162,159,155,147,142,137,136,138,143,160,171,190,197,202,202,202,201,194,189,177,170,158,153,150,148],[231,231,233,235,239,248,252,260,264,273,277,280,282,283],[273,272,271,270,267,262,257,249,243,240,237,235,234,234,233,233],[296,296,297,299,300,301,301,302,303,304,305,306,306,305,304,298,294,286,283,281,281,282,284,284,285,287,290,293,294,299,301,308,309,314,315,316]],
  "y": [[213,213,212,211,210,208,207,206,206,209,212,217,220,227,230,234,236,238,239,239,239,239,239,239,241,247,252,259,261,264,266,269,270,271,271,271,270,269,268],[231,231,232,235,238,246,249,257,261,267,270,272,273,274],[230,230,230,231,234,240,246,258,268,273,277,281,281,283,283,284],[192,192,191,189,188,187,187,187,188,188,190,193,195,198,200,205,208,213,215,215,215,214,214,214,214,216,218,220,221,223,223,223,223,221,221,220]]
  }}}'
```

Parameter

Type

Description

strokes

JSON

Strokes in JSON with appropriate format

strokes\_session\_id (optional)

string

Stroke session ID returned included by [app token API call](#using-client-side-app-tokens)

All other Request Params from v3/text are supported, See [Request parameters](#request-parameters).

Note that the `strokes_session*` information but be sent along with the `app_token` token as a auth header, see [app tokens](#using-client-side-app-tokens). Strokes sessions, meaning digital ink inputs with live updating results, are billed differently from `v3/strokes` requests without intermediate results (no live updates), see the [Mathpix OCR pricing section](https://mathpix.com/ocr#pricing). Note that customers are billed for a live strokes session the first time they send strokes for a given session, not when they request `app_token` and `strokes_session_id`.

## Response body

> Get an API response:

```
{
  "request_id": "cea6b8e40ab4550ac467ce2eb00430be",
  "is_printed": false,
  "is_handwritten": true,
  "auto_rotate_confidence": 0.0020149118193977245,
  "auto_rotate_degrees": 0,
  "confidence": 1,
  "confidence_rate": 1,
  "latex_styled": "3 x^{2}",
  "text": "\\( 3 x^{2} \\)",
  "version": "RSK-M100"
}
```

Field

Type

Description

text (optional)

string

Recognized `text` format, if such is found

confidence (optional)

number in \[0,1\]

Estimated probability 100% correct

confidence\_rate (optional)

number in \[0,1\]

Estimated confidence of output quality

data (optional)

\[object\]

List of data objects (see "Data object" section above)

html (optional)

string

Annotated HTML output

# Process an equation image

> Example image:
> 
> [Image: picture](https://mathpix-ocr-examples.s3.amazonaws.com/limit.jpg)
> 
> JSON request body to send an image URL:

```
{
  "src": "https://mathpix-ocr-examples.s3.amazonaws.com/limit.jpg",
  "formats": ["latex_normal"]
}
```

> Response:

```
{
  "auto_rotate_confidence": 0,
  "auto_rotate_degrees": 0,
  "detection_list": [],
  "detection_map": {
    "contains_chart": 0,
    "contains_diagram": 0,
    "contains_graph": 0,
    "contains_table": 0,
    "is_blank": 0,
    "is_inverted": 0,
    "is_not_math": 0,
    "is_printed": 0
  },
  "image_height": 288,
  "image_width": 720,
  "latex_confidence": 1,
  "latex_confidence_rate": 1,
  "latex_normal": "\\operatorname { lim } _ { x \\rightarrow 3 } ( \\frac { x ^ { 2 } + 9 } { x - 3 } )",
  "position": {
    "height": 279,
    "top_left_x": 54,
    "top_left_y": 9,
    "width": 591
  },
  "request_id": "2025_04_16_8abbb8a58f90328da6b0g",
  "version": "SuperNet-100"
}
```

**POST api.mathpix.com/v3/latex**

Legacy endpoint for processing equation image. Deprecated in favor of **v3/text**.

## Request parameters

> Example request sending an image URL:

```
#!/usr/bin/env python
import requests
import json

data = {
    "src": "https://mathpix-ocr-examples.s3.amazonaws.com/limit.jpg",
    "formats": [
        "latex_simplified",
        "asciimath"
    ]
}
r = requests.post("https://api.mathpix.com/v3/latex",
    json=data,
    headers={
        "app_id": "APP_ID",
        "app_key": "APP_KEY",
        "Content-type": "application/json"
    }
)
print(json.dumps(r.json(), indent=4, sort_keys=True))
```

```
curl -X POST https://api.mathpix.com/v3/latex \
-H 'app_id: APP_ID' \
-H 'app_key: APP_KEY' \
-H 'Content-Type: application/json' \
--data '{"src": "https://mathpix-ocr-examples.s3.amazonaws.com/limit.jpg", "formats": ["latex_simplified", "asciimath"]}'
```

> Send an image file:

```
#!/usr/bin/env python
import requests
import json

r = requests.post("https://api.mathpix.com/v3/latex",
    files={"file": open("limit.jpg","rb")},
    data={"options_json": json.dumps({
        "formats": ["latex_simplified", "asciimath"]
    })},
    headers={
        "app_id": "APP_ID",
        "app_key": "APP_KEY"
    }
)
print(json.dumps(r.json(), indent=4, sort_keys=True))
```

```
curl -X POST https://api.mathpix.com/v3/latex \
-H 'app_id: APP_ID' \
-H 'app_key: APP_KEY' \
--form 'file=@"limit.jpg"' \
--form 'options_json="{\"formats\": [\"latex_simplified\", \"asciimath\"]}"'
```

```
{
  "asciimath": "lim_(x rarr3)((x^(2)+9)/(x-3))",
  "auto_rotate_confidence": 0,
  "auto_rotate_degrees": 0,
  "detection_list": [],
  "detection_map": {
    "contains_chart": 0,
    "contains_diagram": 0,
    "contains_graph": 0,
    "contains_table": 0,
    "is_blank": 0,
    "is_inverted": 0,
    "is_not_math": 0,
    "is_printed": 0
  },
  "image_height": 288,
  "image_width": 720,
  "latex_confidence": 1,
  "latex_confidence_rate": 1,
  "latex_simplified": "\\lim _ { x \\rightarrow 3 } ( \\frac { x ^ { 2 } + 9 } { x - 3 } )",
  "position": {
    "height": 279,
    "top_left_x": 54,
    "top_left_y": 9,
    "width": 591
  },
  "request_id": "2025_04_16_1564713a0a0300b49ca4g",
  "version": "SuperNet-100"
}
```

> You can request multiple formats for a single image:

```
{
  "ocr": ["math", "text"],
  "skip_recrop": true,
  "formats": [
    "text",
    "latex_simplified",
    "latex_styled",
    "mathml",
    "asciimath",
    "latex_list"
  ]
}
```

Parameter

Type

Description

src (optional)

string

Image URL

tags (optional)

\[string\]

Tags are lists of strings that can be used to identify results. see [OCR Results](#ocr-search-parameters)

async (optional)

\[bool\]

This flag is to be used when sending non-interactive requests

formats

string\[\]

String postprocessing formats (see Formatting section)

ocr (optional)

string\[\]

Process only math \["math"\] or both math and text \["math", "text"\]. Default is \["math"\]

format\_options (optional)

object

Options for specific formats (see Formatting section)

skip\_recrop (optional)

bool

Force algorithm to consider whole image

confidence\_threshold (optional)

number in \[0,1\]

Set threshold for triggering confidence errors

beam\_size (optional)

number in \[1,5\]

Number of results to consider during recognition

n\_best (optional)

integer in \[1,beam\_size\]

Number of highest-confidence results to return

region (optional)

object

Specify the image area with the pixel coordinates `top_left_x`, `top_left_y`, `width`, and `height`

callback (optional)

object

[Callback object](#callback-object)

metadata (optional)

object

Key value object

include\_detected\_alphabets (optional)

bool

Return detected alphabets

auto\_rotate\_confidence\_threshold (optional)

number in \[0,1\]

Specifies threshold for auto rotating image to correct orientation; by default it is set to 0.99, can be disabled with a value of 1 (see [Auto rotation](#auto-rotation) section for details)

enable\_blue\_hsv\_filter (optional)

bool

Enables a special mode of image processing where it OCRs blue hue text exclusively, default false.

## Formatting

The following formats can be used in the request:

Format

Description

text

text mode output, with math inside delimiters, eg. `test \(x^2\)`, inline math by default

text\_display

same as `text`, except uses block mode math instead of inline mode when in doubt

latex\_normal

direct LaTeX representation of the input

latex\_styled

modified output to improve the visual appearance such as adding '\\left' and '\\right' around parenthesized expressions that contain tall expressions like subscript or superscript

latex\_simplified

modified output for symbolic processing such as shortening operator names, replacing long division with a fraction, and converting a column of operands into a single formula

latex\_list

output split into a list of simplified strings to help process multiple equations

mathml

the MathML for the recognized math

asciimath

the AsciiMath for the recognized math

wolfram

a string compatible with the Wolfram Alpha engine

## Format options

> To return a more compact `latex_styled` result, one could send the following request:

```
{
  "ocr": ["math", "text"],
  "skip_recrop": true,
  "formats": [
    "text",
    "latex_simplified",
    "latex_styled",
    "mathml",
    "asciimath",
    "latex_list"
  ],
  "format_options": {
    "latex_styled": { "transforms": ["rm_spaces"] }
  }
}
```

> The result for "latex\*styled" would now be  
> \>     `"\\lim*{x \\rightarrow 3}\\left(\\frac{x^{2}+9}{x-3}\\right)"`  
> instead of  
> \>     `"\\lim \_ { x \\rightarrow 3 } \\left( \\frac { x ^ { 2 } + 9 } { x - 3 } \\right)"`

The optional _format\_options_ request parameter allows a request to customize the LaTeX result formats using an object with a format as the property name and the options for that format as the value. The options value may specify the following properties:

Option

Type

Description

transforms

string\[\]

array of transformation names

math\_delims

\[string, string\]

\[begin, end\] delimiters for math mode, for example `\(` and `\)`

displaymath\_delims

\[string, string\]

\[begin, end\] delimiters for displaymath mode, for example `\[` and `\]`

The currently-supported transforms are:

Transform

Description

rm\_spaces

omit spaces around LaTeX groups and other places where spaces are superfluous

rm\_newlines

uses spaces instead of newlines between text lines in paragraphs

rm\_fonts

omit mathbb, mathbf, mathcal, and mathrm commands

rm\_style\_syms

replace styled commands with unstyled versions, e.g., bigoplus becomes oplus

rm\_text

omit text to the left or right of math

long\_frac

convert longdiv to frac

Note that `rm_fonts` and `rm_style_syms` are implicit in `latex_normal`, `latex_simplified`, and `latex_list`. The `long_frac` transformation is implicit in `latex_simplified` and `latex_list`.

## Response body

```
{
  "detection_list": [],
  "detection_map": {
    "contains_chart": 0,
    "contains_diagram": 0,
    "contains_geometry": 0,
    "contains_graph": 0,
    "contains_table": 0,
    "is_inverted": 0,
    "is_not_math": 0,
    "is_printed": 0
  },
  "latex_normal": "\\lim _ { x \\rightarrow 3 } ( \\frac { x ^ { 2 } + 9 } { x - 3 } )",
  "latex_confidence": 0.86757309488734,
  "latex_confidence_rate": 0.9875550770759583,
  "position": {
    "height": 273,
    "top_left_x": 57,
    "top_left_y": 14,
    "width": 605
  }
}
```

Field

Type

Description

text (optional)

string

Recognized `text` format

text\_display (optional)

string

Recognized `text_display` format

latex\_normal (optional)

string

Recognized `latex_normal` format

latex\_simplified (optional)

string

Recognized `latex_normal` format

latex\_styled (optional)

string

Recognized `latex_styled` format

latex\_list (optional)

string\[\]

Recognized `latex_list` format

mathml (optional)

string

Recognized MathML format

asciimath (optional)

string

Recognized AsciiMath format

wolfram (optional)

string

Recognized Wolfram format

position (optional)

object

Position object, pixel coordinates

detection\_list (optional)

string\[\]

Detects image properties (see image properties)

error (optional)

string

US locale error message

error\_info (optional)

object

Error info object

latex\_confidence (optional)

number in \[0,1\]

Estimated probability 100% correct

latex\_confidence\_rate (optional)

number in \[0,1\]

Estimated confidence of output quality

candidates (optional)

object\[\]

n\_best results

detected\_alphabets (optional)

\[object\]

[DetectedAlphabet](/#detectedalphabet-object) object

auto\_rotate\_confidence (optional)

number in \[0,1\]

Estimated probability that image needs to be rotated, see [Auto rotation](#auto-rotation)

auto\_rotate\_degrees (optional)

number in {0, 90, -90, 180}

Estimated angle of rotation in degrees to put image in correct orientation, see [Auto rotation](#auto-rotation)

The `detected_alphabets` result object contains a field that is true of false for each known alphabet. The field is true if any characters from the alphabet are recognized in the image, regardless of whether any of the result fields contain the characters.

Field

Type

Description

en

bool

English

hi

bool

Hindi Devenagari

zh

bool

Chinese

ja

bool

Kana Hiragana or Katakana

ko

bool

Hangul Jamo

ru

bool

Russian

th

bool

Thai

ta

bool

Tamil

te

bool

Telugu

gu

bool

Gujarati

bn

bool

Bengali

## Image properties

The API defines multiple detection types:

Detection

Definition

contains\_diagram

Contains a diagram.

is\_printed

The image is taken of printed math, not handwritten math.

is\_not\_math

No valid equation was detected.

# Query image results

**GET api.mathpix.com/v3/ocr-results**

Mathpix allows customers to search their results from posts to /v3/text, /v3/strokes, and /v3/latex with a GET request on /v3/ocr-results?_search-parameters_.

The search request must also be authenticated the same way OCR requests are, in order to return relevant search results. See [Authorization](#authorization)

Requests with the metadata `improve_mathpix` field set to false will not appear in the search results.

Note that this endpoint will only work with API keys created after July 5th, 2020.

## Request parameters

```
curl -X GET -H 'app_key: APP_KEY' \
    'https://api.mathpix.com/v3/ocr-results?from_date=2021-07-02T18%3A48%3A25.769285%2B00%3A00&page=1&per_page=10&tags=test_tag2&tags=test_tag3&is_handwritten=True'
```

```
{
  "ocr_results": [
    {
      "timestamp": "2021-07-02T18:48:46.080Z",
      "duration": 0.132,
      "endpoint": "/v3/text",
      "request_args": {
        "tags": ["test_tag2", "test_tag3"],
        "formats": ["text"]
      },
      "result": {
        "text": "\\( 12+5 x-8=12 x-10 \\)",
        "confidence": 1,
        "is_printed": false,
        "request_id": "a4301400f66b9821d35cbabea8a26992",
        "is_handwritten": true,
        "confidence_rate": 1,
        "auto_rotate_degrees": 0,
        "auto_rotate_confidence": 0.0027393347044402105,
        "version": "RSK-M100"
      },
      "detections": {
        "contains_chemistry": false,
        "contains_diagram": false,
        "is_handwritten": true,
        "is_printed": false,
        "contains_table": false,
        "contains_triangle": false
      }
    },
    {
      "timestamp": "2021-07-02T18:48:45.903Z",
      "duration": 0.15,
      "endpoint": "/v3/text",
      "request_args": {
        "tags": ["test_tag", "test_tag2", "test_tag3"],
        "formats": ["text"]
      },
      "result": {
        "text": "\\( 12+5 x-8=12 x-10 \\)",
        "confidence": 1,
        "is_printed": false,
        "request_id": "7fe48fb1cd61f8a00ba4e71381740efb",
        "is_handwritten": true,
        "confidence_rate": 1,
        "auto_rotate_degrees": 0,
        "auto_rotate_confidence": 0.0027393347044402105,
        "version": "RSK-M100"
      },
      "detections": {
        "contains_chemistry": false,
        "contains_diagram": false,
        "is_handwritten": true,
        "is_printed": false,
        "contains_table": false,
        "contains_triangle": false
      }
    }
  ]
}
```

Search parameter

Type

Description

page (default=1)

integer

First page of results to return

per\_page (default=100)

integer

Number of results to return

from\_date (optional)

string

starting (included) ISO datetime

to\_date (optional)

string

ending (excluded) ISO datetime

app\_id (optional)

string

results for the given app\_id

text (optional)

string

result.text contains the given string

text\_display (optional)

string

result.text\_display contains the given string

latex\_styled (optional)

string

result.latex\_styled contains the given string

tags (optional)

\[string\]

an array of tag strings

is\_printed (optional)

boolean

All results that contain printed text/math are included

is\_handwritten (optional)

boolean

All results that contain handwritten text/math are included

contains\_table (optional)

boolean

All results that contain a table are included

contains\_chemistry (optional)

boolean

All results that contain chemistry diagrams are included

contains\_diagram (optional)

boolean

All results that contain diagrams are included

contains\_triangle (optional)

boolean

All results that contain triangles are included

## Result object

Field

Type

Description

timestamp

string

ISO timestamp of recorded result information

endpoint

string

API endpoint used for upload (eg `/v3/text`, `/v3/strokes`, ...)

duration

number

Difference between timestamp and when request was received

request\_args

object

Request body arguments

result

object

Result body for request

detections

object

An object of detections for each request

# Query ocr usage

**GET api.mathpix.com/v3/ocr-usage**

To track ocr usage, a user may get information from v3/ocr-usage, adding to the request period of time, and can group responses in different ways.

## Request parameters

```
curl -X 'GET' \
  'https://api.mathpix.com/v3/ocr-usage?from_date=2021-01-01T00%3A00%3A00.000Z&to_date=2021-01-02T00%3A00%3A00.000Z&group_by=usage_type&timespan=month' \
  -H 'app_id: APP_ID' \
  -H 'app_key: APP_KEY'
```

Search parameter

Type

Description

from\_date (optional)

string

starting (included) ISO datetime

to\_date (optional)

string

ending (excluded) ISO datetime

group\_by

string

return values aggregated by this parameter. One of `usage_type`, `request_args_hash`, `app_id`

timespan

string

return aggregated by specified timespan

## Response body

> Get an API response:

```
{
  "ocr_usage": [
    {
      "from_date": "2022-01-01T00:00:00.000Z",
      "app_id": ["mathpix"],
      "usage_type": "image",
      "request_args_hash": ["1f241a3777a5646b98eb4e07c1e39f27770c14d8"],
      "count": 21
    },
    {
      "from_date": "2022-01-01T00:00:00.000Z",
      "app_id": ["mathpix"],
      "usage_type": "image-async",
      "request_args_hash": [
        "05d8e589e40f0e071908e93facd5b3f4a3ec87c0",
        "1402ecaace7d72c61a900f1f1e0d4c729db636e7"
      ],
      "count": 7
    }
  ]
}
```

Field

Type

Description

from\_date

string

starting (included) ISO datetime

usage\_type

string

type of service

request\_args\_hash

string

hash of request\_args

count

number

number of requests according to the selected `group_by` request parameter

# Process a PDF

**POST api.mathpix.com/v3/pdf**

Mathpix supports processing for PDFs, Ebooks, and documents.

Supported inputs:

*   PDF file
*   EPUB file
*   DOCX file
*   PPTX file
*   AZW, AZW3, or KFX file (Kindle formats)
*   MOBI file
*   DJVU file
*   DOC file
*   WPD file (WordPerfect Document)
*   ODT file (OpenDocument Text)

Supported outputs:

*   MMD file ([Mathpix Markdown spec](https://mathpix.com/docs/mathpix-markdown/overview))
*   MD file ([Markdown spec](https://www.markdownguide.org/basic-syntax/))
*   DOCX file (compatible with MS Office, Google Docs, Libre Office)
*   LaTeX zip file (includes images)
*   HTML (rendered Mathpix Markdown content)
*   PDF with HTML (PDF file with HTML rendering)
*   PDF with LaTeX (equations are selectable)

## Request parameters for uploading PDFs

> Send a PDF URL for processing:

```
#!/usr/bin/env python
import requests
import json

r = requests.post("https://api.mathpix.com/v3/pdf",
    json={
        "url": "http://cs229.stanford.edu/notes2020spring/cs229-notes1.pdf",
        "conversion_formats": {
            "docx": True,
            "tex.zip": True
        }
    },
    headers={
        "app_id": "APP_ID",
        "app_key": "APP_KEY",
        "Content-type": "application/json"
    }
)
print(json.dumps(r.json(), indent=4, sort_keys=True))
```

```
curl -X POST https://api.mathpix.com/v3/pdf \
-H 'app_id: APP_ID' \
-H 'app_key: APP_KEY' \
-H 'Content-Type: application/json' \
--data '{ "url": "http://cs229.stanford.edu/notes2020spring/cs229-notes1.pdf", "conversion_formats": {"docx": true, "tex.zip": true}}'
```

You can either send a file URL, or you can upload a file.

Parameter

Type

Description

url (optional)

string

HTTP URL where the file can be downloaded from

streaming (optional)

bool

Whether streaming should be enabled for this request, see [stream pdf pages](#stream-pdf-pages). Default is `false`

metadata (optional)

object

Key value object

alphabets\_allowed (optional)

object

See [AlphabetsAllowed](#alphabetsallowed-object) section, use this to specify which alphabets you don't want in the output

rm\_spaces (optional)

bool

Determines whether extra white space is removed from equations in `latex_styled` and `text` formats. Default is `true`.

rm\_fonts (optional)

bool

Determines whether font commands such as \\mathbf and \\mathrm are removed from equations in `latex_styled` and `text` formats. Default is `false`.

idiomatic\_eqn\_arrays (optional)

bool

Specifies whether to use aligned, gathered, or cases instead of an array environment for a list of equations. Default is `false`.

include\_equation\_tags (optional)

bool

Specifies whether to include equation number tags inside equations LaTeX in the form of `\tag{eq_number}`, where `eq_number` is an equation number (e.g. `1.12`). When set to `true`, it sets `"idiomatic_eqn_arrays": true`, because equation numbering works better in those environments compared to the _array_ environment.

include\_smiles (optional)

bool

Enable experimental chemistry diagram OCR, via RDKIT normalized SMILES with `isomericSmiles=False`, included in `text` output format, via MMD SMILES syntax `<smiles>...</smiles>`. Default is `true`.

include\_chemistry\_as\_image (optional)

bool

Returns an image crop containing the SMILES in the alt-text for chemical diagrams. For example: `![<smiles>CCC</smiles>](https://cdn.mathpix.com/cropped/image_id.jpg)`. Default is `false`.

include\_diagram\_text (optional)

bool

Enables text extraction from diagrams, `false` by default. The extracted text will be part of `lines.json` data, and not part of the `lines.mmd.json` or final mmd. The `parent_id` of these text lines will correspond to the `id` of one of the diagrams in the `lines.json` data.

numbers\_default\_to\_math (optional)

bool

Specifies whether numbers are always math, e.g., `Answer: \( 17 \)` instead of `Answer: 17`. Default is `false`.

math\_inline\_delimiters (optional)

\[string, string\]

Specifies begin inline math and end inline math delimiters for `text` outputs. Default is `["\\(", "\\)"]`.

math\_display\_delimiters (optional)

\[string, string\]

Specifies begin display math and end display math delimiters for `text` outputs. Default is `["\\[", "\\]"]`.

page\_ranges

string

Specifies a page range as a comma-separated string. Examples include `2,4-6` which selects pages \[2,4,5,6\] and `2 - -2` which selects all pages starting with the second page and ending with the next-to-last page (specified by -2)

enable\_spell\_check

bool

Enables a predictive mode for English handwriting that takes word frequencies into account; this option is skipped when the language is not detected as English; incorrectly spelled words that are clearly written will not be changed, this predictive mode is only enabled when the underlying word is visually ambiguous, see [here](https://mathpix.com/docs/ocr/examples#handwritten-text-with-spellcheck) for an example.

auto\_number\_sections

bool

Specifies whether sections and subsections in the output are automatically numbered. Defaults to `false` [note](#pdf-sections).

remove\_section\_numbering

bool

Specifies whether to remove existing numbering for sections and subsections. Defaults to `false` [note](#pdf-sections).

preserve\_section\_numbering

bool

Specifies whether to keep existing section numbering as is. Defaults to `true` [note](#pdf-sections).

enable\_tables\_fallback

bool

Enables advanced table processing algorithm that supports very large and complex tables. Defaults to `false`

fullwidth\_punctuation (optional)

bool

Controls if punctuation will be fullwidth Unicode (default for east Asian languages like Chines), of halfwidth Unicode (default for Latin scripts, Cyrillic scripts etc.). Default value is `null`, which means fullwidth vs halfwidth will be decided based on image content. Punctuation inside math will always stay halfwidth.

conversion\_formats

object

Specifies formats that the v3/pdf output(Mathpix Markdown) should automatically be converted into, on completion. See [Conversion Formats](#conversion-formats).

> Send a PDF file for processing:

```
import requests
import json

options = {
    "conversion_formats": {"docx": True, "tex.zip": True},
    "math_inline_delimiters": ["$", "$"],
    "rm_spaces": True
}
r = requests.post("https://api.mathpix.com/v3/pdf",
    headers={
        "app_id": "APP_ID",
        "app_key": "APP_KEY"
    },
    data={
        "options_json": json.dumps(options)
    },
    files={
        "file": open("css299-notes.pdf","rb")
    }
)
print(r.text.encode("utf8"))
```

```
curl --location --request POST 'https://api.mathpix.com/v3/pdf' \
--header 'app_id: APP_ID' \
--header 'app_key: APP_KEY' \
--form 'file=@"cs229-notes5.pdf"' \
--form 'options_json="{\"conversion_formats\": {\"docx\": true, \"tex.zip\": true}, \"math_inline_delimiters\": [\"$\", \"$\"], \"rm_spaces\": true}"'
```

To send a PDF file simply include the file in the form-data request body.

## Response body

> Reponse to PDF / PDF URL upload

```
{
  "pdf_id": "5049b56d6cf916e713be03206f306f1a"
}
```

Field

Type

Description

pdf\_id

string

Tracking ID to get status and result when completed

error (optional)

string

US locale error message

error\_info (optional)

object

Error info object

## Stream PDF pages

```
# See Python tab for contents of this script
python pdf_stream_test.py
```

```
# Content of pdf_stream_test.py
import httpx
import asyncio
import json
import traceback

BASE_URL = "https://api.mathpix.com/v3/pdf"
# Replace these with your actual endpoint and app key
APP_KEY = "YOUR-APP-KEY"
# Replace with your PDF URL
pdf_url = "http://cs229.stanford.edu/notes2020spring/cs229-notes1.pdf"


async def upload_pdf_url(pdf_url):
    """
    Submits a PDF URL for processing and retrieves the `pdf_id`.
    """
    headers = {"app_key": APP_KEY, "Content-Type": "application/json"}
    payload = {"url": pdf_url, "streaming": True}
    async with httpx.AsyncClient() as client:
        response = await client.post(BASE_URL, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"Upload successful: {data}")
            return data.get("pdf_id")
        else:
            print(f"Failed to upload PDF: {response.status_code}, {response.text}")
            return None

async def stream_pdf(pdf_id):
    """
    Streams the processed PDF data using the `pdf_id`.
    """
    url = f"{BASE_URL}/{pdf_id}/stream"
    headers = {"app_key": APP_KEY}
    async with httpx.AsyncClient() as client:
        try:
            async with client.stream("GET", url, headers=headers) as response:
                if response.status_code == 200:
                    print("Connected to the stream!")
                    async for line in response.aiter_lines():
                        if line.strip():  # Ignore empty lines
                            try:
                                data = json.loads(line)
                                # print(data['text'])
                                last_idx = min(len(data['text']), 10)
                                if last_idx == 10:
                                    data['text'] = data['text'][:10] + "..."
                                print(data)
                            except json.JSONDecodeError:
                                print(f"Failed to decode line: {line}")
                else:
                    print(f"Failed to connect: {response.status_code}")
        except Exception as e:
            print(f"Error: {e}")
            print(traceback.format_exc())

async def main():
    pdf_id = await upload_pdf_url(pdf_url)
    if pdf_id:
        await stream_pdf(pdf_id)

# Run the asyncio function
asyncio.run(main())
```

> The outputs will look like this:

```
{"version": "RSK-M134p10", "text": "\\title{\nCS...", "page_idx": 1, "pdf_selected_len": 28, "pdf_id": "2024_12_15_dfc981061e9740db9fd6g"}
{"version": "RSK-M134p10", "text": "\n\nGiven da...", "page_idx": 2, "pdf_selected_len": 28, "pdf_id": "2024_12_15_dfc981061e9740db9fd6g"}
{"version": "RSK-M134p10", "text": "\n\n\\section...", "page_idx": 3, "pdf_selected_len": 28, "pdf_id": "2024_12_15_dfc981061e9740db9fd6g"}
{"version": "RSK-M134p10", "text": "\n\nNow, giv...", "page_idx": 4, "pdf_selected_len": 28, "pdf_id": "2024_12_15_dfc981061e9740db9fd6g"}
{"version": "RSK-M134p10", "text": "\nfor linea...", "page_idx": 6, "pdf_selected_len": 28, "pdf_id": "2024_12_15_dfc981061e9740db9fd6g"}
```

Certain apps benefit from a lower time to first data. Such apps are recommended to use:

**GET api.mathpix.com/v3/pdf/{pdf\_id}/stream**

which uses server side events (SSE) to improve user experience for real time use cases.

To use this endpoint, you must first set `streaming` to `true` in your POST request to api.mathpix.com/v3/pdf, see [request parameters](#request-parameters-for-uploading-pdfs). Only then will you be able to make the corresponding GET request to stream the page results.

The streaming endpoint enables clients to stream JSON messages with the following fields:

Field

Type

Description

text

string

Mathpix Markdown output

page\_idx

number

page index from selected page range, starting at 1 and going all the way to `pdf_selected_len`

pdf\_selected\_len

number

total number of pages inside selected page range

The stream provides one JSON object at a time per page. Note that the pages are not guaranteed to be in order, although they generally will be in order.

## Processing status

```
curl --location --request GET 'https://api.mathpix.com/v3/pdf/PDF_ID' \
--header 'app_key: APP_KEY' \
--header 'app_id: APP_ID'
```

> Response after a few seconds:

```
{
  "status": "split",
  "num_pages": 9,
  "percent_done": 11.11111111111111,
  "num_pages_completed": 1
}
```

> Response after a few more seconds:

```
{
  "status": "completed",
  "num_pages": 9,
  "percent_done": 100,
  "num_pages_completed": 9
}
```

To check the processing status of a PDF, use the `pdf_id` returned from the initial request and append it to `/v3/pdf` in a GET request.

**GET https://api.mathpix.com/v3/pdf/{pdf\_id}**

Field

Type

Description

status

string

Processing status, will be `received` upon successful request, `loaded` if PDF was down-loaded onto our servers, `split` when PDF pages are split and sent for processing, `completed` when PDF is done processing, or `error` if a problem occurs during processing

num\_pages (optional)

integer

Total number of pages in PDF document

num\_pages\_completed (optional)

integer

Current number of pages in PDF document that have been OCR-ed

percent\_done (optional)

number

Percentage of pages in PDF that have been OCR-ed

## Get conversion status

```
# Replace {pdf_id} with your pdf_id
curl --location --request GET 'https://api.mathpix.com/v3/converter/{pdf_id}' \
--header 'app_key: APP_KEY' \
--header 'app_id: APP_ID'
```

> Response after a few seconds:

```
{
  "status": "completed",
  "conversion_status": {
    "docx": {
        "status": "processing"
    },
    "tex.zip": {
        "status": "processing"
    }
}
```

> Response after a few more seconds:

```
{
  "status": "completed",
  "conversion_status": {
    "docx": {
        "status": "completed"
    },
    "tex.zip": {
        "status": "completed"
    }
}
```

To get the status of your conversions, use the following endpoint:

**GET https://api.mathpix.com/v3/converter/{pdf\_id}**

The response object is described here:

Field

Type

Description

status

string

`completed` for an existing mmd document

conversion\_status (optional)

object

{\[format\]: {status: "processing" | "completed" | "error", error\_info?: {id, error}}}

## Conversion results

> Save results to local mmd file, md file, docx file, HTML, and LaTeX zip

```
curl --location --request GET 'https://api.mathpix.com/v3/pdf/{pdf_id}.mmd' \
--header 'app_key: APP_KEY' \
--header 'app_id: APP_ID' > {pdf_id}.mmd

curl --location --request GET 'https://api.mathpix.com/v3/pdf/{pdf_id}.docx' \
--header 'app_key: APP_KEY' \
--header 'app_id: APP_ID' > {pdf_id}.docx

curl --location --request GET 'https://api.mathpix.com/v3/pdf/{pdf_id}.tex' \
--header 'app_key: APP_KEY' \
--header 'app_id: APP_ID' > {pdf_id}.tex.zip

curl --location --request GET 'https://api.mathpix.com/v3/pdf/{pdf_id}.html' \
--header 'app_key: APP_KEY' \
--header 'app_id: APP_ID' > {pdf_id}.html

curl --location --request GET 'https://api.mathpix.com/v3/pdf/{pdf_id}.lines.json' \
--header 'app_key: APP_KEY' \
--header 'app_id: APP_ID' > {pdf_id}.lines.json

curl --location --request GET 'https://api.mathpix.com/v3/pdf/{pdf_id}.lines.mmd.json' \
--header 'app_key: APP_KEY' \
--header 'app_id: APP_ID' > {pdf_id}.lines.mmd.json
```

```
import requests

pdf_id = "PDF_ID"
headers = {
  "app_key": "APP_KEY",
  "app_id": "APP_ID"
}

# get mmd response
url = "https://api.mathpix.com/v3/pdf/" + pdf_id + ".mmd"
response = requests.get(url, headers=headers)
with open(pdf_id + ".mmd", "w") as f:
    f.write(response.text)

# get docx response
url = "https://api.mathpix.com/v3/pdf/" + pdf_id + ".docx"
response = requests.get(url, headers=headers)
with open(pdf_id + ".docx", "wb") as f:
    f.write(response.content)

# get LaTeX zip file
url = "https://api.mathpix.com/v3/pdf/" + pdf_id + ".tex"
response = requests.get(url, headers=headers)
with open(pdf_id + ".tex.zip", "wb") as f:
    f.write(response.content)

# get HTML file
url = "https://api.mathpix.com/v3/pdf/" + pdf_id + ".html"
response = requests.get(url, headers=headers)
with open(pdf_id + ".html", "wb") as f:
    f.write(response.content)

# get lines data
url = "https://api.mathpix.com/v3/pdf/" + pdf_id + ".lines.json"
response = requests.get(url, headers=headers)
with open(pdf_id + ".lines.json", "wb") as f:
    f.write(response.content)

# get lines mmd json
url = "https://api.mathpix.com/v3/pdf/" + pdf_id + ".lines.mmd.json"
response = requests.get(url, headers=headers)
with open(pdf_id + ".lines.mmd.json", "wb") as f:
    f.write(response.content)
```

Once a PDF has been fully OCR-ed, resulting in `status=completed`, you can get the mmd result and line-by-line data by adding `.mmd` or `.lines.json` to the status GET request. Conversion formats such as `docx` and `tex.zip` will not be available until the format status is `completed`.

The possible values of the extension are described here.

Extension

Description

mmd

Returns Mathpix Markdown text file

md

Returns plain Markdown text file

docx

Returns a docx file

tex.zip

Returns a LaTeX zip file

latex.pdf

Returns a PDF file with LaTeX rendering

pdf

Returns a PDF file with HTML rendering

html

Returns a HTML file with the rendered Mathpix Markdown content

lines.json

Returns [line by line data](#pdf-lines-data)

lines.mmd.json

Returns [line by line mmd data](#pdf-mmd-lines-data), deprecated please use `lines.json` which contains all this information and more.

Note that the `tex.zip` extension downloads a zip file containing the main `.tex` file and any images that appear in the document.

## PDF lines data

> To get line by line data with geometric information about PDF content:

```
curl --location --request GET 'https://api.mathpix.com/v3/pdf/PDF_ID.lines.json' \
--header 'app_key: APP_KEY' \
--header 'app_id: APP_ID' > {pdf_id}.lines.json
```

```
import requests

pdf_id = "PDF_ID"
headers = {
  "app_key": "APP_KEY",
  "app_id": "APP_ID"
}

# get json lines data
url = "https://api.mathpix.com/v3/pdf/" + pdf_id + ".lines.json"
response = requests.get(url, headers=headers)
with open(pdf_id + ".lines.json", "w") as f:
    f.write(response.text)
```

> Response:

```
{
  "pages": [
    {
      "image_id": "2025_04_16_0add99e0b17361a86393g-01",
      "page": 1,
      "lines": [
        {
          "cnt": [[755,656],[755,585],[1370,585],[1370,656]],
          "region": {
            "top_left_x": 754,
            "top_left_y": 585,
            "width": 617,
            "height": 71
          },
          "line": 1,
          "column": 0,
          "font_size": 56,
          "is_printed": true,
          "is_handwritten": false,
          "id": "2d11b98adea840d998bc2ac078479dfd",
          "type": "title",
          "conversion_output": false,
          "children_ids": [
            "c85dad31ba3d4064bff33b8d026b020e"
          ],
          "text": "",
          "text_display": ""
        },
        {
          "cnt": [[752,655],[752,592],[1362,592],[1362,655]],
          "region": {
            "top_left_x": 752,
            "top_left_y": 592,
            "width": 611,
            "height": 63
          },
          "line": 2,
          "column": 0,
          "font_size": 56,
          "is_printed": true,
          "is_handwritten": false,
          "id": "c85dad31ba3d4064bff33b8d026b020e",
          "type": "text",
          "conversion_output": true,
          "parent_id": "2d11b98adea840d998bc2ac078479dfd",
          "text": "CS229 Lecture Notes",
          "text_display": "\\title{\nCS229 Lecture Notes\n}",
          "confidence": 1,
          "confidence_rate": 1
        },
        {
          "cnt": [[786,890],[786,725],[1328,725],[1328,890]],
          "region": {
            "top_left_x": 786,
            "top_left_y": 725,
            "width": 543,
            "height": 166
          },
          "line": 3,
          "column": 0,
          "font_size": 44,
          "is_printed": true,
          "is_handwritten": false,
          "id": "219813849c8a47b080b00c81b899f7d1",
          "type": "authors",
          "conversion_output": false,
          "children_ids": [
            "e354b20aec6d450482776283b939b79c",
            "02f43a91aff54759aa337c075ae43808"
          ],
          "text": "",
          "text_display": ""
        },
        {
          "cnt": [[935,785],[935,733],[1184,733],[1184,785]],
          "region": {
            "top_left_x": 935,
            "top_left_y": 733,
            "width": 250,
            "height": 52
          },
          "line": 4,
          "column": 0,
          "font_size": 44,
          "is_printed": true,
          "is_handwritten": false,
          "id": "e354b20aec6d450482776283b939b79c",
          "type": "text",
          "conversion_output": true,
          "parent_id": "219813849c8a47b080b00c81b899f7d1",
          "text": "Andrew Ng",
          "text_display": "\n\n\\author{\nAndrew Ng",
          "confidence": 0.9951171875,
          "confidence_rate": 0.999650434513919
        },
        {
          "cnt": [[790,886],[790,827],[1324,827],[1324,886]],
          "region": {
            "top_left_x": 790,
            "top_left_y": 826,
            "width": 535,
            "height": 61
          },
          "line": 5,
          "column": 0,
          "font_size": 44,
          "is_printed": true,
          "is_handwritten": false,
          "id": "02f43a91aff54759aa337c075ae43808",
          "type": "text",
          "conversion_output": true,
          "parent_id": "219813849c8a47b080b00c81b899f7d1",
          "text": "(updates by Tengyu Ma)",
          "text_display": " \\\\ (updates by Tengyu Ma)\n}",
          "confidence": 1,
          "confidence_rate": 1
        }
      ]
    }
  ]
}
```

Mathpix provides detailed line by line data for PDFs. This can be useful for building novel user experiences on top of original PDFs.

### Response data object

Field

Type

Description

pages

[PdfPageData](#pdfpagedata-object)

List of PdfPageData objects

### PdfPageData object

Field

Type

Description

image-id

string

PDF ID, plus hyphen, plus page number, starting at page 1

page

integer

Page number

lines

[PdfLineData](#pdflinedata-object)

List of LineData objects

page\_height

integer

Page height (in pixel coordinates)

page\_width

integer

Page width (in pixel coordinates)

### PdfLineData object

Field

Type

Description

id

string

Unique line identifier

parent\_id (optional)

string

Unique line identifier of the parent.

children\_ids (optional)

\[string\]

List of children unique identifiers.

type

string

See [line types and subtypes](#line-data-types-and-subtypes) for details.

subtype (optional)

string

See [line types and subtypes](#line-data-types-and-subtypes) for details.

line

integer

Line number

text

string

Searchable text, empty string for page elements that do not necessarily have associated text (for example individual equations inside block of math equations).

text\_display

string

Mathpix Markdown content with additional contextual elements such as `article`, `section` and inline image URLs. Can be empty for page elements which are not going to be rendered (for example page number, auxiliary text in the page header, etc.).

conversion\_output

boolean

When `true`, `text_display` from the line is included into final MMD output, otherwise it is not included.

is\_printed

boolean

True if line contains printed text, false otherwise.

is\_handwritten

boolean

True if line contains handwritten text, false otherwise.

region

object

Specify the image area with the pixel coordinates `top_left_x`, `top_left_y`, `width`, and `height`

cnt

\[\[x,y\]\]

Specifies the image area as list of (x,y) pixel coordinate pairs. This captures handwritten content much better than a region object

confidence

number in \[0,1\]

Estimated probability 100% correct (product of per token OCR confidence).

confidence\_rate

number in \[0,1\]

Estimated confidence of output quality (geometric mean of per token OCR confidence).

## PDF MMD lines data

> To get line by line data containing geometric and contextual information from a PDF:

```
curl --location --request GET 'https://api.mathpix.com/v3/pdf/{pdf_id}.lines.mmd.json' \
--header 'app_key: APP_KEY' \
--header 'app_id: APP_ID' > {pdf_id}.lines.mmd.json
```

```
import requests

pdf_id = "PDF_ID"
headers = {
  "app_key": "APP_KEY",
  "app_id": "APP_ID"
}

# get json lines data
url = "https://api.mathpix.com/v3/pdf/" + pdf_id + ".lines.mmd.json"
response = requests.get(url, headers=headers)
with open(pdf_id + ".lines.mmd.json", "w") as f:
    f.write(response.text)
```

> Response:

```
{
  "pages": [
    {
      "image_id": "2022_04_27_5bd0e5ee1dbf53cc68c1g-1",
      "page": 1,
      "page_height": 1651,
      "page_width": 1275,
      "lines": [
        {
          "cnt": [
            [448, 395],
            [448, 351],
            [818, 351],
            [818, 395]
          ],
          "region": {
            "top_left_x": 448,
            "top_left_y": 351,
            "height": 45,
            "width": 371
          },
          "is_printed": true,
          "is_handwritten": false,
          "text": "\\title{\nCS229 Lecture Notes\n}",
          "line": 1
        },
        {
          "cnt": [
            [554, 469],
            [554, 434],
            [712, 434],
            [712, 469]
          ],
          "region": {
            "top_left_x": 554,
            "top_left_y": 434,
            "height": 36,
            "width": 159
          },
          "is_printed": true,
          "is_handwritten": false,
          "text": "\n\n\\author{\nAndrew Ng",
          "line": 2
        },
        {
          "cnt": [
            [476, 537],
            [476, 492],
            [795, 492],
            [795, 537]
          ],
          "region": {
            "top_left_x": 476,
            "top_left_y": 492,
            "height": 46,
            "width": 320
          },
          "is_printed": true,
          "is_handwritten": false,
          "text": " \\\\ (updates by Tengyu Ma)\n}",
          "line": 3
        }
      ]
    }
  ]
}
```

### Response data object (MMD Lines)

Field

Type

Description

pages

[PdfMMDPageData](#pdfmmdpagedata-object)

List of PdfMMDPageData objects

### PdfMMDPageData object

Field

Type

Description

image-id

string

PDF ID, plus hyphen, plus page number, starting at page 1

page

integer

Page number

lines

[PdfMMDLineData](#pdfmmdlinedata-object)

List of PageMMDLineData objects

page\_height

integer

Page height (in pixel coordinates)

page\_width

integer

Page width (in pixel coordinates)

### PdfMMDLineData object

Field

Type

Description

line

integer

Line number

text

string

Mathpix Markdown content with additional contextual elements such as `article`, `section` and inline image URLs

is\_printed

boolean

True if line contains printed text, false otherwise.

is\_handwritten

boolean

True if line contains handwritten text, false otherwise.

region

object

Specify the image area with the pixel coordinates `top_left_x`, `top_left_y`, `width`, and `height`

cnt

\[\[x,y\]\]

Specifies the image area as list of (x,y) pixel coordinate pairs. This captures handwritten content much better than a region object

confidence

number in \[0,1\]

Estimated probability 100% correct (product of per token OCR confidence).

confidence\_rate

number in \[0,1\]

Estimated confidence of output quality (geometric mean of per token OCR confidence).

## Deleting PDF results

To delete a PDF’s output data, use the `DELETE` method on the same URL used for retrieving the PDF status or document (e.g., `/v3/pdf/{ID}`).

When a PDF is deleted:

*   All output files are permanently removed from our servers, including:
    *   The MMD file
    *   All associated images
    *   The JSON Lines (structured data)
    *   Any other output formats that may have been requested
*   These files become inaccessible and links to them will break.
*   The original input PDF file is also deleted from our servers.
*   This deletion is permanent and cannot be undone.

When a PDF is deleted, we retain minimal metadata for internal tracking and usage analytics. This includes:

*   PDF `status` (always shown as `complete` after deletion; if a PDF has not finished processing, attempting to delete it will return a 404 error)
*   `input_file` name (e.g., `example.pdf`)
*   `num_pages`, `num_pages_completed`
*   Timestamps: `created_at`, `deleted_at`
*   version of the processing engine

This metadata is kept for auditing, billing, and API usage tracking purposes. No output content is stored.

# Convert Documents

**POST api.mathpix.com/v3/converter**

If you want to convert an MMD document to other formats, you can do a POST to the `/v3/converter` endpoint with the mmd text and desired formats.

The available conversion formats are:

*   `md`
*   `docx`
*   `tex.zip`
*   `html`
*   `pdf`
*   `latex.pdf`

## Request parameters

> Send an MMD document for conversion:

```
curl -X POST https://api.mathpix.com/v3/converter \
-H 'app_id: APP_ID' \
-H 'app_key: APP_KEY' \
-H 'Content-Type: application/json' \
--data '{ "mmd": "_full mmd text_", "formats": {"docx": true, "tex.zip": true}}'
```

```
import requests
import json

url = "https://api.mathpix.com/v3/converter"

payload = json.dumps({
  "mmd": "_full mmd text_",
  "formats": {
    "docx": True,
    "tex.zip": True
  }
})
headers = {
  'app_id': 'APP_ID',
  'app_key': 'APP_KEY',
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.json())
```

Parameter

Type

Description

mmd

string

MMD document that needs to be converted into other formats

formats

object

Specifies output formats. See [Conversion Formats](#conversion-formats).

conversion\_options (optional)

object

Specifies options for specific output formats. Each key corresponds to a format enabled in formats, and the associated object contains format-specific settings. See [Conversion Options](#conversion-options).

The maximum JSON body in a conversion request is 10MB.

## Response body

> Reponse to a POST v3/converter request

```
{
  "conversion_id": "5049b56d6cf916e713be03206f306f1a"
}
```

The result is just like a PDF request except returning `conversion_id` instead of `pdf_id`. You use the `conversion_id` in a GET to `/v3/converter/conversion_id`.

## Conversion Formats

```
{
  "md": false,
  "docx": false,
  "tex.zip": true,
  "html": true,
  "pdf": false,
  "latex.pdf": false
}
```

Conversion formats used for `v3/pdf` `conversion_formats` and `v3/converter` `formats`.

## Conversion Options

Conversion options used for `v3/pdf` `conversion_options` and `v3/converter` `conversion_options`.

Specifies options for specific output [formats](#conversion-formats). Each key corresponds to a format enabled in formats, and the associated object contains format-specific settings.

### Conversion options for docx

```
  "formats": {
    "docx": true
  },
  "conversion_options": {
    "docx": {
        "font": "Times New Roman",
        "fontSize": "28",
        "language": "auto",
        "orientation": "portrait",
        "margins": {
            "top": "1440",
            "right": "1800",
            "bottom": "1440",
            "left": "1800",
            "gutter": "0"
        }
    }
  }
```

Parameter

Type

Description

font (optional)

string

Specifies the name of the font that will be used in the document. Default is `Georgia`.

fontSize (optional)

integer

Specifies the font size in half-points. Default is `22` (which is `11 pt` in a document).

language (optional)

string

Specifies the document language. You can explicitly specify the language, for example `English (US)`, `German`. Sets the language for checking spelling and grammar in the document. Default is `auto` (language is detected automatically).

orientation (optional)

string

Specifies the page orientation `portrait` or `landscape`. Default is `portrait`.

margins (optional)

object

Specifies page margins. All values are in twips (1 twip = 1/20 of a point).  
top (integer) — Top margin. Default is `1440`.  
right (integer) — Right margin. Default is `1800`.  
bottom (integer) — Bottom margin. Default is `1440`.  
left (integer) — Left margin. Default is `1800`.  
gutter (integer, optional) — Extra space for binding. Default is `0`.

**Note:** Supported language values:  
`auto`, `Afrikaans`, `Arabic`, `Basque (Basque)`, `Bosnian`, `Bulgarian`, `Catalan`, `Chinese (China)`, `Chinese (Taiwan)`, `Croatian`, `Czech`, `Danish`, `Dutch`, `English (AUS)`, `English (CAN)`, `English (UK)`, `English (US)`, `Estonian`, `Finnish`, `French`, `French (Canada)`, `French (Switzerland)`, `Galician`, `German`, `German (Austria)`, `German (Switzerland)`, `Greek`, `Gujarati`, `Hebrew`, `Hindi`, `Hungarian`, `Icelandic`, `Indonesian`, `Irish`, `isiXhosa`, `isiZulu`, `Italian`, `Japanese`, `Kannada`, `Kazakh`, `Kiswahili`, `Korean`, `Latvian`, `Lithuanian`, `Macedonian`, `Malaysian`, `Marathi`, `Norwegian Borkmal`, `Norwegian Nynorsk`, `Persian`, `Polish`, `Portuguese`, `Portuguese (Brazil)`, `Romanian`, `Russian`, `Serbian (Cyrillic)`, `Serbian (Latin)`, `Sesotho Sa Leboa`, `Setswana`, `Slovak`, `Slovenian`, `Spanish`, `Spanish (Traditional Sort)`, `Swedish`, `Tamil`, `Telugu`, `Thai`, `Turkish`, `Ukrainian`, `Welsh`.

### Conversion options for tex.zip

```
  "formats": {
    "tex.zip": true
  },
  "conversion_options": {
    "tex.zip": {
        "fontSize": "12pt",
        "imagesFolder": "media",
        "font": "Crimson Text"
    }
  }
```

Parameter

Type

Description

fontSize (optional)

string

Specifies the font size. Default is `10pt`.

font (optional)

string

Specifies the name of the font that will be used in the document. Default is `CMU Serif`. Used only for `XeLaTeX`[note](#tex-xelatex). Possible values: `CMU Serif`, `Open Sans`, `Crimson Text`, `Arimo`, `Noto Sans`, `Noto Serif`.

imagesFolder (optional)

string

Specifies the folder name for images. Default is `images`.

load\_external\_fonts (optional)

bool

Specifies that all used fonts should be included in the tex.zip. Default is `false`. Used only for `XeLaTeX`[note](#tex-xelatex).

### Conversion options for html

```
  "formats": {
    "html": true
  },
  "conversion_options": {
    "html": {
        "htmlTags": "true"
    }
  }
```

Parameter

Type

Description

htmlTags (optional)

bool

Enables or disables support for HTML tags in the source content. Default is `true`.

### Conversion options for md

```
  "formats": {
    "md": true
  },
  "conversion_options": {
    "md": {
        "math_inline_delimiters": ["$","$"],
        "math_display_delimiters": ["$$","$$"],
        "escape_ampersand": "true",
        "escape_dollar": "true",
        "escape_hash": "true",
        "escape_percent": "false"
    }
  }
```

Parameter

Type

Description

math\_inline\_delimiters (optional)

\[string, string\]

Specifies begin inline math and end inline math delimiters. Default is `["$", "$"]`.

math\_display\_delimiters (optional)

\[string, string\]

Specifies begin display math and end display math delimiters. Default is `["$$", "$$"]`.

escape\_ampersand (optional)

bool

Specifies whether to escape the `&` character in the source content. Default is `true`.

escape\_dollar (optional)

bool

Specifies whether to escape the `$` character in the source content. Default is `true`.

escape\_hash (optional)

bool

Specifies whether to escape the `#` character in the source content. Default is `true`.

escape\_percent (optional)

bool

Specifies whether to escape the `%` character in the source content. Default is `false`.

### Conversion options for latex.pdf

```
  "formats": {
    "latex.pdf": true
  },
  "conversion_options": {
    "latex.pdf": {
        "fontSize": "12pt",
        "font": "Crimson Text"
    }
  }
```

Parameter

Type

Description

fontSize (optional)

string

Specifies the font size in px. Default is `10pt`.

font (optional)

string

Specifies the name of the font that will be used in the document. Default is `CMU Serif`. Used only for `XeLaTeX`[note](#latex-pdf-xelatex). Possible values: `CMU Serif`, `Open Sans`, `Crimson Text`, `Arimo`, `Noto Sans`, `Noto Serif`.

### Conversion options for pdf

```
  "formats": {
    "pdf": true
  },
  "conversion_options": {
    "pdf": {
        "fontSize": "14",
        "text_color": "black",
        "background_color": "white",
        "disable_footer": "true",
        "margin": "40",
        "custom_css": "h1 {font-size: 28px !important;}"
    }
  }
```

Parameter

Type

Description

fontSize (optional)

integer

Specifies the font size. Default is `17`.

text\_color (optional)

string

Specifies the text color, can be name, hex, or rgb. Default is `#1E2029`.

background\_color (optional)

string

Specifies the background color, can be name, hex, or rgb. Default is not set.

disable\_footer (optional)

bool

Enable or disable footer such as page numbers. Default is `false`.

margin (optional)

integer

Specifies the margin size. Minimum value is `40`, maximum is `200`. Default is `70`.

custom\_css (optional)

string

Specifies custom CSS styles to be applied to the document. Default is not set.

footnote\_compact\_refs

bool

Specifies the option to hide repeat indexes for Markdown footnotes. Default is `false`.

## Get conversion status

```
curl --location --request GET 'https://api.mathpix.com/v3/converter/CONVERSION_ID' \
--header 'app_key: APP_KEY' \
--header 'app_id: APP_ID'
```

> Response after a few seconds:

```
{
  "status": "completed",
  "conversion_status": {
    "docx": {
        "status": "processing"
    },
    "tex.zip": {
        "status": "processing"
    }
}
```

> Response after a few more seconds:

```
{
  "status": "completed",
  "conversion_status": {
    "docx": {
        "status": "completed"
    },
    "tex.zip": {
        "status": "completed"
    }
}
```

To get the status of your conversions, use the following endpoint:

**GET https://api.mathpix.com/v3/converter/<CONVERSION\_ID>**

The response object is described here:

Field

Type

Description

status

string

`completed` for an existing mmd document

conversion\_status (optional)

object

{\[format\]: {status: "processing" | "completed" | "error", error\_info?: {id, error}}}

## Conversion results

> Save results to local MD file, DOCX file, HTML, and LaTeX zip

```
curl --location --request GET 'https://api.mathpix.com/v3/converter/CONVERSION_ID.md' \
--header 'app_key: APP_KEY' \
--header 'app_id: APP_ID' > CONVERSION_ID.md

curl --location --request GET 'https://api.mathpix.com/v3/converter/CONVERSION_ID.docx' \
--header 'app_key: APP_KEY' \
--header 'app_id: APP_ID' > CONVERSION_ID.docx

curl --location --request GET 'https://api.mathpix.com/v3/converter/CONVERSION_ID.tex.zip' \
--header 'app_key: APP_KEY' \
--header 'app_id: APP_ID' > CONVERSION_ID.tex.zip

curl --location --request GET 'https://api.mathpix.com/v3/converter/CONVERSION_ID.html' \
--header 'app_key: APP_KEY' \
--header 'app_id: APP_ID' > CONVERSION_ID.html
```

```
import requests

conversion_id = "CONVERSION_ID"
headers = {
  "app_key": "APP_KEY",
  "app_id": "APP_ID"
}

# get md response
url = "https://api.mathpix.com/v3/converter/" + conversion_id + ".md"
response = requests.get(url, headers=headers)
with open(conversion_id + ".md", "w") as f:
    f.write(response.text)

# get docx response
url = "https://api.mathpix.com/v3/converter/" + conversion_id + ".docx"
response = requests.get(url, headers=headers)
with open(conversion_id + ".docx", "wb") as f:
    f.write(response.content)

# get LaTeX zip file
url = "https://api.mathpix.com/v3/converter/" + conversion_id + ".tex.zip"
response = requests.get(url, headers=headers)
with open(conversion_id + ".tex.zip", "wb") as f:
    f.write(response.content)

# get HTML file
url = "https://api.mathpix.com/v3/converter/" + conversion_id + ".html"
response = requests.get(url, headers=headers)
with open(conversion_id + ".html", "wb") as f:
    f.write(response.content)
```

Once the format status is completed you can download the content by adding the format extension to the `conversion_id`, e.g., GET `/v3/converter/conversion_id.docx`.

Extension

Description

mmd

Returns Mathpix Markdown text file

md

Returns plain Markdown text file

docx

Returns a docx file

tex.zip

Returns a LaTeX zip file

html

Returns a HTML file with the rendered Mathpix Markdown content

latex.pdf

Returns a PDF file with LaTeX rendering

pdf

Returns a PDF file with HTML rendering

Note that the `tex.zip` extension downloads a zip file containing the main `.tex` file and any images that appear in the document.

# Query PDF results

Mathpix allows customers to search their results from posts to /v3/pdf with a GET request on /v3/pdf-results?_search-parameters_. The search request must contain a valid app\_key header to identify the group owning the results to search.

## Request parameters

```
curl -X GET -H 'app_key: APP_KEY' \
    'https://api.mathpix.com/v3/pdf-results?per_page=100&from_date=2020-06-26T03%3A08%3A22.827Z'
```

Query parameter

Type

Description

page (default=1)

integer

First page of results to return

per\_page (default=100)

integer

Number of results to return

from\_date (optional)

string

starting (included) ISO datetime

to\_date (optional)

string

ending (excluded) ISO datetime

app\_id (optional)

string

results for the given app\_id

## Query result object

```
{
  "pdfs": [
    {
      "id": "113cee229ab27b715b7cc24cfdbb2c33",
      "input_file": "https://s3.amazonaws.com/mathpix-ocr-examples/authors_0.pdf",
      "status": "completed",
      "created_at": "2020-06-26T03:08:23.827Z",
      "modified_at": "2020-06-26T03:08:27.827Z",
      "num_pages": 1,
      "num_pages_completed": 1,
      "request_args": {}
    },
    {
      "id": "9ad69e94346e65047215d25709760f29",
      "input_file": "https://s3.amazonaws.com/mathpix-ocr-examples/1457.pdf",
      "status": "completed",
      "created_at": "2020-06-27T03:08:23.827Z",
      "modified_at": "2020-06-27T03:08:27.827Z",
      "num_pages": 1,
      "num_pages_completed": 1,
      "request_args": {}
    }
  ]
}
```

Field

Type

Description

id

string

ID of the processed PDF

input\_file

string

The URL or the filename of the processed PDF

created\_at

string

ISO timestamp of when the PDF was received

modified\_at

string

ISO timestamp of when the PDF finished processing

num\_pages

integer

Number of pages in the request PDF

num\_pages\_completed

integer

Number of pages of the PDF that were processed

request\_args

object

Request body arguments

# Process a batch

> An equation image batch request is made with JSON that looks like:

```
{
  "urls": {
    "inverted": "https://raw.githubusercontent.com/Mathpix/api-examples/master/images/inverted.jpg",
    "algebra": "https://raw.githubusercontent.com/Mathpix/api-examples/master/images/algebra.jpg"
  },
  "formats": ["latex_simplified"]
}
```

```
curl -X POST https://api.mathpix.com/v3/batch \
-H "app_id: APP_ID" \
-H "app_key: APP_KEY" \
-H "Content-Type: application/json" \
--data '{ "urls": {"inverted": "https://raw.githubusercontent.com/Mathpix/api-examples/master/images/inverted.jpg", "algebra": "https://raw.githubusercontent.com/Mathpix/api-examples/master/images/algebra.jpg"},"formats":["latex_simplified"] }'
```

```

import requests
import json

base_url = "https://raw.githubusercontent.com/Mathpix/api-examples/master/images/"

r = requests.post(
    "https://api.mathpix.com/v3/batch",
    json={
        "urls": {
            "algebra": base_url + "algebra.jpg",
            "inverted": base_url + "inverted.jpg"
        },
        "formats": ["latex_simplified"]
    },
    headers={
        "app_id": "APP_ID",
        "app_key": "APP_KEY",
        "content-type": "application/json"
    },
    timeout=30
)
reply = r.json()
assert "batch_id" in reply
```

> The response to the batch is a positive integer value for `batch_id`.

```
{
  "batch_id": "17"
}
```

> The response to GET /v3/batch/17 is below when the batch has completed. Before completion the "results" field may be empty or contain only one of the two results.

```
{
  "keys": ["algebra", "inverted"],
  "results": {
    "algebra": {
      "detection_list": [],
      "detection_map": {
        "contains_chart": 0,
        "contains_diagram": 0,
        "contains_geometry": 0,
        "contains_graph": 0,
        "contains_table": 0,
        "is_inverted": 0,
        "is_not_math": 0,
        "is_printed": 0
      },
      "latex_simplified": "12 + 5 x - 8 = 12 x - 10",
      "latex_confidence": 0.99640350138238,
      "position": {
        "height": 208,
        "top_left_x": 0,
        "top_left_y": 0,
        "width": 1380
      }
    },
    "inverted": {
      "detection_list": ["is_inverted", "is_printed"],
      "detection_map": {
        "contains_chart": 0,
        "contains_diagram": 0,
        "contains_geometry": 0,
        "contains_graph": 0,
        "contains_table": 0,
        "is_inverted": 1,
        "is_not_math": 0,
        "is_printed": 1
      },
      "latex_simplified": "x ^ { 2 } + y ^ { 2 } = 9",
      "latex_confidence": 0.99982263230866,
      "position": {
        "height": 170,
        "top_left_x": 48,
        "top_left_y": 85,
        "width": 544
      }
    }
  }
}
```

**POST api.mathpix.com/v3/batch**

The Mathpix API supports processing multiple equation images in a single POST request to a different endpoint: `/v3/batch`. The request body may contain any `/v3/latex` parameters except `src` and must also contain a `urls` parameter. The request may also contain an additonal `callback` parameter to receive results after all the images in the batch have been processed.

Parameter

Type

Description

urls

object

key-value for each image in the batch where the value may be a string url or an object containing a url and image-specific options such as `region` and `formats`.

ocr\_behavior (optional)

string

`text` for processing like [`v3/text`](#process-an-image) or the default `latex` for processing like [`v3/latex`](#process-an-equation-image)

callback (optional)

object

description of where to send the batch results. [Callback object](#callback-object)

The response contains only a unique `batch_id` value. Even if the request includes a callback, there is no guarantee the callback will run successfuly (because of a transient network failure, for example). The preferred approach is to wait an appropriate length of time (about one second for every five images in the batch) and then do a GET on `/v3/batch/:id` where :id is the `batch_id` value. The GET request must contain the same `app_id` and `app_key` headers as the POST to `/v3/batch`.

The GET response has the following fields:

Field

Type

Description

keys

string\[\]

all the url keys present in the originating batch request

results

object

an OCR result for each key that has been processed

## Process images as a batch with `v3/text` behavior

The `ocr_behavior` param can be set to `text` to enable images to be processed with `v3/text` behavior. As with batch, all params can either be set at the top level or set individually.

> Setting `ocr_behavior` and other `v3/text` params at the top level

```
{
  "urls": {
    "inverted": "https://raw.githubusercontent.com/Mathpix/api-examples/master/images/inverted.jpg",
    "algebra": "https://raw.githubusercontent.com/Mathpix/api-examples/master/images/algebra.jpg"
  },
  "ocr_behavior": "text",
  "formats": ["text", "html", "data"],
  "data_options": { "include_asciimath": true }
}
```

> Setting `ocr_behavior` and other `v3/text` params individually.

```
{
  "urls": {
    "inverted": {
      "url": "https://raw.githubusercontent.com/Mathpix/api-examples/master/images/inverted.jpg",
      "ocr_behavior": "text",
      "formats": ["text", "html", "data"],
      "data_options": { "include_asciimath": true }
    },
    "algebra": {
      "url": "https://raw.githubusercontent.com/Mathpix/api-examples/master/images/algebra.jpg",
      "ocr_behavior": "text",
      "formats": ["text", "html", "data"],
      "data_options": { "include_asciimath": true }
    }
  }
}
```

> Make a batch request with `v3/text` behavior.

```
curl -X POST https://api.mathpix.com/v3/batch \
-H "app_id: APP_ID" \
-H "app_key: APP_KEY" \
-H "Content-Type: application/json" \
--data-raw '{
  "urls": {
    "inverted": "https://raw.githubusercontent.com/Mathpix/api-examples/master/images/inverted.jpg",
    "algebra": "https://raw.githubusercontent.com/Mathpix/api-examples/master/images/algebra.jpg"
  },
  "ocr_behavior": "text",
  "formats": ["text", "html", "data"],
  "data_options": { "include_asciimath": true }
}'
```

```

import requests
import json

base_url = "https://raw.githubusercontent.com/Mathpix/api-examples/master/images/"

r = requests.post(
    "https://api.mathpix.com/v3/batch",
    json={
        "urls": {
            "algebra": base_url + "algebra.jpg",
            "inverted": base_url + "inverted.jpg"
        },
        "ocr_behavior": "text",
        "formats": ["text", "html", "data"],
        "data_options": { "include_asciimath": True }
    },
    headers={
        "app_id": "APP_ID",
        "app_key": "APP_KEY",
        "content-type": "application/json"
    },
    timeout=30
)
reply = r.json()
assert "batch_id" in reply
```

> The response to the batch is a positive integer value for `batch_id`.

```
{
  "batch_id": "17"
}
```

> The response to GET /v3/batch/17 is below when the batch has completed. Before completion the "results" field may be empty or contain only one of the two results.

```
{
  "keys": ["inverted", "algebra"],
  "results": {
    "inverted": {
      "request_id": "2022_11_14_f985002323de848eb848g",
      "version": "RSK-M104",
      "image_width": 676,
      "image_height": 340,
      "is_printed": true,
      "is_handwritten": false,
      "auto_rotate_confidence": 0.0008788120718712378,
      "auto_rotate_degrees": 0,
      "confidence": 1,
      "confidence_rate": 1,
      "text": "\\( x^{2}+y^{2}=9 \\)",
      "html": "<div><span class=\"math-inline \">\n<asciimath style=\"display: none;\">x^(2)+y^(2)=9</asciimath></span></div>\n",
      "data": [
        {
          "type": "asciimath",
          "value": "x^(2)+y^(2)=9"
        }
      ]
    },
    "algebra": {
      "request_id": "2022_11_14_f985002323de848eb848g",
      "version": "RSK-M104",
      "image_width": 1381,
      "image_height": 209,
      "is_printed": false,
      "is_handwritten": true,
      "auto_rotate_confidence": 0,
      "auto_rotate_degrees": 0,
      "confidence": 1,
      "confidence_rate": 1,
      "text": "\\( 12+5 x-8=12 x-10 \\)",
      "html": "<div><span class=\"math-inline \">\n<asciimath style=\"display: none;\">12+5x-8=12 x-10</asciimath></span></div>\n",
      "data": [
        {
          "type": "asciimath",
          "value": "12+5x-8=12 x-10"
        }
      ]
    }
  }
}
```

# Callback object

Field

Type

Description

post

string

url to post results

reply (optional)

object

data to send in reply to batch POST

body (optional)

object

data to send with results

headers (optional)

object

headers to use when posting results

# Supported image types

Mathpix supports image types compatible with [OpenCV](https://docs.opencv.org/4.5.2/d4/da8/group__imgcodecs.html), including:

*   JPEG files - \_.jpeg, \_.jpg, \*.jpe
*   Portable Network Graphics - \*.png
*   Windows bitmaps - \_.bmp, \_.dib
*   JPEG 2000 files - \*.jp2
*   WebP - \*.webp
*   Portable image format - \_.pbm, \_.pgm, \_.ppm \_.pxm, \*.pnm
*   PFM files - \*.pfm
*   Sun rasters - \_.sr, \_.ras
*   TIFF files - \_.tiff, \_.tif
*   OpenEXR Image files - \*.exr
*   Radiance HDR - \_.hdr, \_.pic
*   Raster and Vector geospatial data supported by GDAL

# Error handling

All requests will return `error` and `error_info` fields if an argument is missing or incorrect, or if some problem happens while processing the request. The `error` field contains an en-us string describing the error. The `error_info` field contains an object providing programmatic information.

## Error info object

Field

Type

Description

id

string

specifies the error id (see below)

message

string

error message

detail (optional)

object

Additional error info

## Error id strings

Id

Description

Detail fields

HTTP Status

http\_unauthorized

Invalid credentials

401

http\_max\_requests

Too many requests

count

429

json\_syntax

JSON syntax error

200

image\_missing

Missing URL in request body

200

image\_download\_error

Error downloading image

url

200

image\_decode\_error

Cannot decode the image data

200

image\_no\_content

No content found in image

200

image\_not\_supported

Image is not math or text

200

image\_max\_size

Image is too large to process

200

strokes\_missing

Missing strokes in request body

200

strokes\_syntax\_error

Incorrect JSON or strokes format

200

strokes\_no\_content

No content found in strokes

200

opts\_bad\_callback

Bad callback field(s)

post?, reply?, batch\_id?

200

opts\_unknown\_ocr

Unknown ocr option(s)

ocr

200

opts\_unknown\_format

Unknown format option(s)

formats

200

opts\_number\_required

Option must be a number

name,value

200

opts\_value\_out\_of\_range

Value not in accepted range

name,value

200

pdf\_encrypted

PDF is encrypted and not readable

200

pdf\_unknown\_id

PDF ID expired or isn't

200

pdf\_missing

Request sent without url field

200

pdf\_page\_limit\_exceeded

PDF exceeds maximum page limit

200

math\_confidence

Low confidence

200

math\_syntax

Unrecognized math

200

batch\_unknown\_id

Unknown batch id

batch\_id

200

sys\_exception

Server error

200

sys\_request\_too\_large

Max request size is 5mb for images and 512kb for strokes

200

# Privacy

> Example of a request with the extra privacy setting:

```
{
  "metadata": {
    "improve_mathpix": false
  }
}
```

By default we make images accessible to our QA team so that we can make improvements.

We also provide an extra privacy option which ensures that no image data or derived information is ever persisted to disk, and no data is available to Mathpix's QA team (we still track the request and how long the request took to complete). Simply add a metadata object to the main request body with the `improve_mathpix` field set to `false` (by default it is `true`). Note that this option means that images and results will not be accessible via Mathpix Console (console.mathpix.com).

# Long division

> Response for image on the left side:

```
{
  "detection_map": {
    "contains_chart": 0,
    "contains_diagram": 0,
    "contains_geometry": 0,
    "contains_graph": 0,
    "contains_table": 0,
    "is_inverted": 0,
    "is_not_math": 0,
    "is_printed": 1
  },
  "latex_normal": "8 \\longdiv { 7200 }"
}
```

We use the special markup `\longdiv` to represent long division; it is the only nonvalid Latex markup we return. Long division is used much like `\sqrt` which is visually similar.

[Image: No description](https://raw.githubusercontent.com/Mathpix/api-examples/master/images/long_division.jpg)

# Latency considerations

The biggest source of latency is image uploads. The speed of a response from Mathpix API servers is roughly proportional to the size of the image. Try to use images under 100kb for maximum speeds. JPEG compression and image downsizing are recommended to ensure lowest possible latencies.

# Supported math commands

Mathpix can generate any of the following LaTeX commands:

\\#

\\$

\\%

\\&

\\AA

\\Delta

\\Gamma

\\Im

\\Lambda

\\Leftarrow

\\Leftrightarrow

\\Longleftarrow

\\Longleftrightarrow

\\Longrightarrow

\\Omega

\\Perp

\\Phi

\\Pi

\\Psi

\\Re

\\Rightarrow

\\S

\\Sigma

\\Theta

\\Upsilon

\\Varangle

\\Vdash

\\Xi

\\\\

\\aleph

\\alpha

\\angle

\\approx

\\asymp

\\atop

\\backslash

\\because

\\begin

\\beta

\\beth

\\bigcap

\\bigcirc

\\bigcup

\\bigodot

\\bigoplus

\\bigotimes

\\biguplus

\\bigvee

\\bigwedge

\\boldsymbol

\\bot

\\bowtie

\\breve

\\bullet

\\cap

\\cdot

\\cdots

\\check

\\chi

\\circ

\\circlearrowleft

\\circlearrowright

\\circledast

\\cline

\\complement

\\cong

\\coprod

\\cup

\\curlyvee

\\curlywedge

\\curvearrowleft

\\curvearrowright

\\dagger

\\dashv

\\dddot

\\ddot

\\ddots

\\delta

\\diamond

\\div

\\dot

\\doteq

\\dots

\\downarrow

\\ell

\\emptyset

\\end

\\epsilon

\\equiv

\\eta

\\exists

\\fallingdotseq

\\forall

\\frac

\\frown

\\gamma

\\geq

\\geqq

\\geqslant

\\gg

\\ggg

\\gtrless

\\gtrsim

\\hat

\\hbar

\\hline

\\hookleftarrow

\\hookrightarrow

\\imath

\\in

\\infty

\\int

\\iota

\\jmath

\\kappa

\\lambda

\\langle

\\lceil

\\ldots

\\leadsto

\\leftarrow

\\leftleftarrows

\\leftrightarrow

\\leftrightarrows

\\leftrightharpoons

\\leq

\\leqq

\\leqslant

\\lessdot

\\lessgtr

\\lesssim

\\lfloor

\\ll

\\llbracket

\\llcorner

\\lll

\\longdiv

\\longleftarrow

\\longleftrightarrow

\\longmapsto

\\longrightarrow

\\lrcorner

\\ltimes

\\mapsto

\\mathbb

\\mathbf

\\mathcal

\\mathfrak

\\mathrm

\\mathscr

\\mho

\\models

\\mp

\\mu

\\multicolumn

\\multimap

\\multirow

\\nVdash

\\nabla

\\nearrow

\\neg

\\neq

\\newline

\\nexists

\\ni

\\nmid

\\not

\\notin

\\nprec

\\npreceq

\\nsim

\\nsubseteq

\\nsucc

\\nsucceq

\\nsupseteq

\\nu

\\nvdash

\\nwarrow

\\odot

\\oiiint

\\oiint

\\oint

\\omega

\\ominus

\\operatorname

\\oplus

\\oslash

\\otimes

\\overbrace

\\overleftarrow

\\overleftrightarrow

\\overline

\\parallel

\\partial

\\perp

\\phi

\\pi

\\pitchfork

\\pm

\\prec

\\preccurlyeq

\\preceq

\\precsim

\\prime

\\prod

\\propto

\\psi

\\qquad

\\quad

\\rangle

\\rceil

\\rfloor

\\rho

\\rightarrow

\\rightleftarrows

\\rightleftharpoons

\\rightrightarrows

\\rightsquigarrow

\\risingdotseq

\\rrbracket

\\rtimes

\\searrow

\\sigma

\\sim

\\simeq

\\smile

\\sqcap

\\sqcup

\\sqrt

\\sqsubset

\\sqsubseteq

\\sqsupset

\\sqsupseteq

\\square

\\stackrel

\\star

\\subset

\\subseteq

\\subsetneq

\\succ

\\succcurlyeq

\\succeq

\\succsim

\\sum

\\supset

\\supseteq

\\supseteqq

\\supsetneq

\\supsetneqq

\\swarrow

\\tau

\\textrm

\\therefore

\\theta

\\tilde

\\times

\\top

\\triangle

\\triangleleft

\\triangleq

\\triangleright

\\underbrace

\\underline

\\underset

\\unlhd

\\unrhd

\\uparrow

\\uplus

\\vDash

\\varepsilon

\\varliminf

\\varlimsup

\\varnothing

\\varphi

\\varpi

\\varrho

\\varsigma

\\varsubsetneqq

\\vartheta

\\vdash

\\vdots

\\vec

\\vee

\\wedge

\\widehat

\\widetilde

\\wp

\\xi

\\zeta

\\{

\\|

\\}

# System status

You can check the status of MathpixOCR and other systems at https://status.mathpix.com

[cURL](#) [Python](#)