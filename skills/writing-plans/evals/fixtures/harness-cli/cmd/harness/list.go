package main

import (
	"fmt"
	"io"
	"os"
	"text/tabwriter"
	"time"

	"github.com/spf13/cobra"
)

// Row is one line of `harness list` output.
type Row struct {
	Name      string
	Status    string
	UpdatedAt time.Time
}

var statusFilter string

func newListCmd(out io.Writer, fetch func() ([]Row, error)) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List registered harnesses",
		RunE: func(cmd *cobra.Command, args []string) error {
			rows, err := fetch()
			if err != nil {
				return err
			}
			rows = filterRows(rows, statusFilter)
			if len(rows) == 0 {
				return fmt.Errorf("no harnesses match")
			}
			return printTable(out, rows)
		},
	}
	cmd.Flags().StringVar(&statusFilter, "status", "", "only show rows with this status")
	return cmd
}

func filterRows(rows []Row, status string) []Row {
	if status == "" {
		return rows
	}
	var kept []Row
	for _, r := range rows {
		if r.Status == status {
			kept = append(kept, r)
		}
	}
	return kept
}

func printTable(out io.Writer, rows []Row) error {
	w := tabwriter.NewWriter(out, 0, 4, 2, ' ', 0)
	fmt.Fprintln(w, "NAME\tSTATUS\tUPDATED")
	for _, r := range rows {
		fmt.Fprintf(w, "%s\t%s\t%s\n", r.Name, r.Status, r.UpdatedAt.Format(time.RFC3339))
	}
	return w.Flush()
}

func main() {
	root := &cobra.Command{Use: "harness"}
	root.AddCommand(newListCmd(os.Stdout, fetchRows))
	if err := root.Execute(); err != nil {
		os.Exit(1)
	}
}
