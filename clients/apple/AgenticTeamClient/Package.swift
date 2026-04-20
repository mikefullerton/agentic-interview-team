// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "AgenticTeamClient",
    platforms: [
        .macOS(.v14),
    ],
    products: [
        .library(
            name: "AgenticTeamClient",
            type: .dynamic,
            targets: ["AgenticTeamClient"]
        ),
    ],
    targets: [
        .target(
            name: "AgenticTeamClient",
            path: "Sources/AgenticTeamClient",
            swiftSettings: [
                .enableExperimentalFeature("StrictConcurrency"),
            ]
        ),
        .testTarget(
            name: "AgenticTeamClientTests",
            dependencies: ["AgenticTeamClient"],
            path: "Tests/AgenticTeamClientTests"
        ),
    ]
)
