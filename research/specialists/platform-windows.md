# Windows Platform Specialist

## Domain Coverage
WinUI 3, Fluent Design, MSIX packaging, High DPI/display scaling, MVVM, theming (light/dark/high-contrast), .NET/C#, Narrator, UI Automation.

## Cookbook Sources
- `cookbook/guidelines/platform/windows/`
- `cookbook/guidelines/language/csharp/`

## Structured Questions

1. Describe your WinUI version strategy. On WinUI 3? If not, what's preventing migration?

2. How do you approach high DPI displays? Tested on 4K? What broke?

3. Walk me through your MVVM architecture. Navigation? Keeping ViewModels from knowing about Views?

4. What's your theming strategy? Dark mode? High Contrast? Runtime switching?

5. How do you manage localization on Windows? .resw files? How many languages? Tested RTL?

6. Describe your dependency injection setup. Microsoft.Extensions.DependencyInjection? How are services registered?

7. Custom controls — when create vs. style built-in controls?

8. MSIX packaging process. Who signs? How do you distribute updates?

9. Capabilities and permissions — which do you request? How do users understand why?

10. Async/await approach — deadlock issues? How do you test async code?

11. Supporting multiple languages with text expansion — what breaks? Layouts flexible enough?

12. Ensuring performance on older hardware — test on low-end devices?

## Exploratory Prompts

1. Why does Fluent Design emphasize simplicity and focus? What assumptions about desktop apps is that challenging?

2. What if you had to support every DPI from 96 to 500 without custom pixel fiddling? How would you think about scaling?

3. If nullable reference types are enabled, what does that tell you about the code's intent?

4. Why is "use TextFillColorPrimary" better than "use #FFFFFF"? What's the relationship between semantic colors and maintainability?
