# AZ_DSCommon Code Overview

The `AZ_DSCommon` repository is a Play Framework 1.2+ library that extends the framework with tooling for docflow documents, security and CRUD forms. The codebase mixes Java server components with AngularJS client code compiled via Gulp.

## Directory Structure
- **app/** – main application sources
  - **controllers/** – HTTP controllers for docflow operations (e.g. `DocflowHttpGetController`, `DocflowHttpListController`). `DocflowControllerBase.java` sets CORS headers and handles exceptions.
  - **docflow/** – configuration and messages for the docflow engine. Includes YAML document definitions and `DocflowMessages.java` which contains message templates for validation and HTTP responses.
  - **models/** – document models like `BuiltInUser` and `DocflowFile`. These classes extend the Docflow document base classes and define fields, states and actions.
  - **ngApp/** – AngularJS modules written in CoffeeScript. Built client code is placed under `static/ngApp/js` via Gulp tasks defined in `build.coffee`.
- **conf/** – Play configuration such as `application.conf`.
- **static/** – compiled client assets and third‑party libraries.

## Example Code Snippets
`DocflowControllerBase` prepares responses for CORS and converts exceptions into HTTP errors:
```java
@Before
public static void addCORSHeaders() {
    response.setHeader("Access-Control-Allow-Origin", "*");
    response.setHeader("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept");
}
```
`DocflowMessages` defines reusable templates for responses and validation errors:
```java
public static final MessageTemplate error_HttpConcurrency_4 = new MessageTemplate(
    Result.Error,
    "Document '%1$s' was modified in parallel by '%3$s'.  Please, repeate your action.",
    "DOCFLOWMESSAGES.HTTPCONCURRENCY");
```
`DocflowFile` is an example of a document model with states, filters and actions:
```java
@Entity(name = "doc_docflow_file")
public class DocflowFile extends DocumentSimple {
    @Id
    @GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "doc_docflow_file_seq")
    public long id;
    @Column(length = 100, nullable = false)
    public String filename = "";
    @Column(length = 2000, nullable = false)
    public String title = "";
    public enum States { NEW("new", 0), PERSISTED("persisted", 1); }
}
```

The build system uses `gulpfile.coffee` and `build.coffee` to compile CoffeeScript and bundle client scripts.
