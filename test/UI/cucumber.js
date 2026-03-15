module.exports = {
    default: {
        requireModule: ["ts-node/register"],
        require: [
            "support/**/*.ts",
            "features/step_definitions/**/*.ts"
        ],
        paths: ["features/**/*.feature"],
        format: ["progress", "summary"],
        publishQuiet: true
    }
};