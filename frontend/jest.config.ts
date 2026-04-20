import type { Config } from "jest";
import nextJest from "next/jest";

const config: Config = {
  clearMocks: true,
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/$1"
  },
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],
  testEnvironment: "jest-environment-jsdom"
};

const createJestConfig = nextJest({
  dir: "./"
});

export default createJestConfig(config);
