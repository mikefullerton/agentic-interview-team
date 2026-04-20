import Foundation

public actor TeamSession {
    public let team: String
    private let locator: AtpLocator
    private let teamsRoot: URL?
    private let dispatcher: Dispatcher

    public enum Dispatcher: String, Sendable {
        case mock
        case claudeCode = "claude-code"
    }

    public init(
        team: String,
        locator: AtpLocator = .auto,
        teamsRoot: URL? = nil,
        dispatcher: Dispatcher = .claudeCode
    ) throws {
        self.team = team
        self.locator = try locator.resolved()
        self.teamsRoot = teamsRoot
        self.dispatcher = dispatcher
    }

    public func plan(goal: String) async throws -> String {
        var args = ["plan", team, "--goal", goal, "--dispatcher", dispatcher.rawValue]
        if let db = temporaryDB() { args.append(contentsOf: ["--db", db.path]) }
        let output = try await AtpProcess.runCapturing(locator: locator, teamsRoot: teamsRoot, arguments: args)
        guard let roadmapID = output.split(separator: "\n").last.map(String.init), roadmapID.hasPrefix("rm_") else {
            throw TeamError.unexpectedOutput(output)
        }
        return roadmapID
    }

    public func run(roadmapID: String) -> AsyncThrowingStream<TeamEvent, Error> {
        AsyncThrowingStream { continuation in
            Task {
                do {
                    let args = ["run", team, "--dispatcher", dispatcher.rawValue]
                    try await AtpProcess.stream(locator: locator, teamsRoot: teamsRoot, arguments: args) { line in
                        if let event = TeamEvent.decode(line) {
                            continuation.yield(event)
                        }
                    }
                    continuation.finish()
                } catch {
                    continuation.finish(throwing: error)
                }
            }
        }
    }

    public func rollcall() async throws -> [RollcallEntry] {
        let args = ["rollcall", team, "--format", "json"]
        let output = try await AtpProcess.runCapturing(locator: locator, teamsRoot: teamsRoot, arguments: args)
        return output.split(separator: "\n").compactMap { RollcallEntry.decode(String($0)) }
    }

    public func describe() async throws -> String {
        try await AtpProcess.runCapturing(locator: locator, teamsRoot: teamsRoot, arguments: ["describe", team])
    }

    private func temporaryDB() -> URL? {
        let dir = FileManager.default.temporaryDirectory
        return dir.appendingPathComponent("atp-\(UUID().uuidString).sqlite")
    }
}

public enum TeamError: Error, Sendable {
    case atpNotFound
    case subprocessFailed(code: Int32, stderr: String)
    case unexpectedOutput(String)
}
