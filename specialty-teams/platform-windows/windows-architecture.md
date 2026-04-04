---
name: windows-architecture
description: MVVM with CommunityToolkit.Mvvm — source-generated `ObservableObject`, `RelayCommand`, and messaging; NavigationView + F...
artifact: guidelines/platform/windows/architecture.md
version: 1.0.0
---

## Worker Focus
MVVM with CommunityToolkit.Mvvm — source-generated `ObservableObject`, `RelayCommand`, and messaging; NavigationView + Frame for page-level navigation; navigation service abstraction in ViewModel layer (never manipulate Frame from code-behind); use Template Studio for project scaffolding

## Verify
`[ObservableObject]` and `[RelayCommand]` source generators used; no Frame manipulation in code-behind; navigation service interface injected into ViewModels; `INotifyPropertyChanged` not hand-implemented
