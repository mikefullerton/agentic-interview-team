import Foundation

enum AtpProcess {
    static func runCapturing(
        locator: AtpLocator,
        teamsRoot: URL?,
        arguments: [String]
    ) async throws -> String {
        let process = makeProcess(locator: locator, teamsRoot: teamsRoot, arguments: arguments)
        let stdout = Pipe()
        let stderr = Pipe()
        process.standardOutput = stdout
        process.standardError = stderr
        try process.run()
        process.waitUntilExit()
        let out = String(data: stdout.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? ""
        if process.terminationStatus != 0 {
            let err = String(data: stderr.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? ""
            throw TeamError.subprocessFailed(code: process.terminationStatus, stderr: err)
        }
        return out.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    static func stream(
        locator: AtpLocator,
        teamsRoot: URL?,
        arguments: [String],
        onLine: @Sendable (String) -> Void
    ) async throws {
        let process = makeProcess(locator: locator, teamsRoot: teamsRoot, arguments: arguments)
        let stdout = Pipe()
        let stderr = Pipe()
        process.standardOutput = stdout
        process.standardError = stderr
        try process.run()

        var buffer = Data()
        while process.isRunning {
            let chunk = stdout.fileHandleForReading.availableData
            if chunk.isEmpty { try await Task.sleep(nanoseconds: 50_000_000); continue }
            buffer.append(chunk)
            while let newline = buffer.firstIndex(of: 0x0A) {
                let line = buffer.subdata(in: 0..<newline)
                buffer.removeSubrange(0...newline)
                if let text = String(data: line, encoding: .utf8), !text.isEmpty {
                    onLine(text)
                }
            }
        }
        if process.terminationStatus != 0 {
            let err = String(data: stderr.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? ""
            throw TeamError.subprocessFailed(code: process.terminationStatus, stderr: err)
        }
    }

    private static func makeProcess(
        locator: AtpLocator,
        teamsRoot: URL?,
        arguments: [String]
    ) -> Process {
        let process = Process()
        process.executableURL = locator.python
        var args = [locator.cli.path]
        if let root = teamsRoot {
            args.append(contentsOf: ["--teams-root", root.path])
        }
        args.append(contentsOf: arguments)
        process.arguments = args
        return process
    }
}
