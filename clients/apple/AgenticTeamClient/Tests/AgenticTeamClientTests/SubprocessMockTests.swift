import XCTest
@testable import AgenticTeamClient

final class SubprocessMockTests: XCTestCase {
    func testPlanMockReturnsRoadmapID() async throws {
        let repoRoot = Self.repoRoot()
        let session = try TeamSession(
            team: "devteam",
            teamsRoot: repoRoot.appendingPathComponent("teams"),
            dispatcher: .mock
        )
        let id = try await session.plan(goal: "tiny calculator")
        XCTAssertTrue(id.hasPrefix("rm_"), "expected rm_ prefix, got \(id)")
    }

    private static func repoRoot() -> URL {
        // Tests run from <repo>/clients/apple/AgenticTeamClient; walk up two levels.
        var url = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
        for _ in 0..<10 {
            if FileManager.default.fileExists(atPath: url.appendingPathComponent("teams/devteam").path) {
                return url
            }
            url.deleteLastPathComponent()
        }
        fatalError("repo root not found from \(FileManager.default.currentDirectoryPath)")
    }
}
