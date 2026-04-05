using System.Reflection;

namespace Midi8BitSynthesiser.Tests.TestData;

public static class RepoRootLocator
{
    public static string Find() => FindRepoRoot();

    public static string FindRepoRoot() => GetRequiredMetadata("RepoRoot");

    public static string FindSharedRoot() => GetRequiredMetadata("SharedRoot");

    public static string FindSharedScriptPath() => Path.Combine(FindSharedRoot(), "midi_to_wave.py");

    private static string GetRequiredMetadata(string key)
    {
        var value = typeof(RepoRootLocator).Assembly
            .GetCustomAttributes<AssemblyMetadataAttribute>()
            .FirstOrDefault(attribute => attribute.Key == key)
            ?.Value;

        if (string.IsNullOrWhiteSpace(value))
        {
            throw new DirectoryNotFoundException($"Missing assembly metadata for '{key}'.");
        }

        return value;
    }
}
