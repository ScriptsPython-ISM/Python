import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from tqdm import tqdm

class InvasiveSeaweedModel:
    def __init__(self, grid_size=(100, 100), depth_threshold=40):
        """
        Initialize the invasive seaweed model.
        """
        self.monthly_temp = [13.3, 12.8, 13.1, 14.4, 17.3, 20.9, 21.9, 22.5, 21.9, 19.3, 17.4, 15]
        self.grid_size = grid_size
        self.depth_threshold = depth_threshold
        
        self.seaweed_grid = np.zeros(grid_size, dtype=int)
        self.land_grid = np.zeros(grid_size, dtype=bool)   
        self.depth_grid = np.zeros(grid_size)            
        self.temp_grid = np.zeros(grid_size)           
        
        self.base_growth_rate = 0.2
        self.max_spread_dist = 3
        
        self.history = []
        
    def initialize_environment(self, land_map=None, depth_map=None, initial_seaweed=None):
        """
        Set up the environment variables: land, depth, and initial seaweed positions.
        """
        if land_map is not None:
            self.land_grid = land_map
        else:
            y, x = np.ogrid[:self.grid_size[0], :self.grid_size[1]]
            center = (self.grid_size[0] // 2, self.grid_size[1] // 2)
            dist = np.sqrt((x - center[1])**2 + (y - center[0])**2)
            self.land_grid = dist < min(self.grid_size) // 5
        
        if depth_map is not None:
            self.depth_grid = depth_map
        else:
            self.depth_grid = self._generate_simple_depth_map()
        
        if initial_seaweed:
            for x, y in initial_seaweed:
                if not self.land_grid[y, x] and self.depth_grid[y, x] < self.depth_threshold:
                    self.seaweed_grid[y, x] = 1
        else:
            for _ in range(5):
                while True:
                    x, y = np.random.randint(0, self.grid_size[1]), np.random.randint(0, self.grid_size[0])
                    if not self.land_grid[y, x] and self.depth_grid[y, x] < 50:
                        self.seaweed_grid[y, x] = 1
                        break
        
        self.history.append(self.seaweed_grid.copy())
    
    def _generate_simple_depth_map(self):
        """Generate a simplified depth map based on distance from land."""
        depth_map = np.zeros(self.grid_size)
        
        for y in range(self.grid_size[0]):
            for x in range(self.grid_size[1]):
                if self.land_grid[y, x]:
                    depth_map[y, x] = 0
                else:
                    min_dist = float('inf')
                    for ly in range(self.grid_size[0]):
                        for lx in range(self.grid_size[1]):
                            if self.land_grid[ly, lx]:
                                dist = np.sqrt((x - lx)**2 + (y - ly)**2)
                                min_dist = min(min_dist, dist)
                    
                    depth_map[y, x] = min_dist * 5
        
        return depth_map
    
    def update_temperature(self, month):
        """
        Update water temperature based on the month (0-11 for Jan-Dec)
        """
        for y in range(self.grid_size[0]):
            for x in range(self.grid_size[1]):
                if not self.land_grid[y, x]:
                    
                    temp = self.monthly_temp[month]
                    self.temp_grid[y, x] = temp
                else:
                    self.temp_grid[y, x] = 0 
    
    def calculate_growth_probability(self, y, x, month):
        """
        Calculate probability of seaweed growth at a location based on environmental factors.
        """
        # Return 0 probability for land cells or cells too deep
        if self.land_grid[y, x] or self.depth_grid[y, x] > self.depth_threshold:
            return 0
        
        # Temperature effect (optimal above 15°C)
        temp = self.temp_grid[y, x]
        if temp<15:
            return 0
        else:
            temp_factor = 1 - 15/temp/20 * np.random.choice([0,1], p = [0.0001, 0.9999])
        
        # Depth effect (growth declines with depth)
        if 20 > self.depth_grid[y,x] > 10:
            depth_factor = 1
        else:
            depth_factor = 1 - self.depth_grid[y, x] / self.depth_threshold
        
        probability = self.base_growth_rate * temp_factor * depth_factor
        
        return probability
    
    def simulate_step(self, month):
        """
        Simulate one step
        """
        self.update_temperature(month)
        
        new_grid = self.seaweed_grid.copy()
        
        # For each cell without seaweed, check if it gets colonized
        for y in range(self.grid_size[0]):
            for x in range(self.grid_size[1]):
                # Skip land and existing seaweed
                if self.land_grid[y, x] or self.seaweed_grid[y, x] == 1:
                    continue
                
                # Check neighborhood for seaweed sources
                has_nearby_seaweed = False
                for dy in range(-self.max_spread_dist, self.max_spread_dist + 1):
                    for dx in range(-self.max_spread_dist, self.max_spread_dist + 1):
                        ny, nx = y + dy, x + dx
                        
                        # Check bounds and distance
                        if (0 <= ny < self.grid_size[0] and 0 <= nx < self.grid_size[1] and
                            np.sqrt(dy**2 + dx**2) <= self.max_spread_dist and 
                            self.seaweed_grid[ny, nx] == 1):
                            
                            # Spread probability decreases with distance
                            dist_factor = 1 - np.sqrt(dy**2 + dx**2) / self.max_spread_dist
                            spread_prob = self.calculate_growth_probability(y, x, month) * dist_factor
                            
                            if np.random.random() < spread_prob:
                                new_grid[y, x] = 1
                                break
                    
                    if new_grid[y, x] == 1:
                        break
        
        self.seaweed_grid = new_grid
        self.history.append(self.seaweed_grid.copy())
    
    def simulate(self, num_years=1, steps_per_year=12):
        """
        Simulate model over num_years with steps_per_year iterations per year
        """
        total_steps = num_years * steps_per_year
        
        for step in tqdm(range(total_steps)):
            month = step % steps_per_year
            self.simulate_step(month)
    
    def visualize(self, time_step=-1, show_depth=False, show_temp=False):
        """
        Visualise the current state of seaweed
        """
        fig, axes = plt.subplots(1, 3 if show_depth and show_temp else 2 if show_depth or show_temp else 1, 
                               figsize=(15, 5))
        
        if not isinstance(axes, np.ndarray):
            axes = np.array([axes])
        
        ax = axes[0]
        combined_map = np.zeros(self.grid_size, dtype=int)
        combined_map[self.land_grid] = 1
        combined_map[~self.land_grid & (self.history[time_step] == 1)] = 2
        
        cmap = ListedColormap(['lightblue', 'green', 'red'])
        im = ax.imshow(combined_map, cmap=cmap)
        ax.set_title('Seaweed Distribution')
        
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='lightblue', label='Sea'),
            Patch(facecolor='green', label='Land'),
            Patch(facecolor='red', label='Seaweed')
        ]
        ax.legend(handles=legend_elements, loc='upper right')
        
        plot_idx = 1
        
        # Plot depth map if requested
        if show_depth:
            ax = axes[plot_idx]
            plot_idx += 1
            im = ax.imshow(self.depth_grid, cmap='Blues')
            ax.set_title('Depth Map (meters)')
            plt.colorbar(im, ax=ax)
        
        # Plot temperature map if requested
        if show_temp:
            ax = axes[plot_idx]
            im = ax.imshow(self.temp_grid, cmap='coolwarm')
            ax.set_title('Temperature Map (°C)')
            plt.colorbar(im, ax=ax)
        
        plt.tight_layout()
        plt.show()
    
    def create_animation(self, filename='seaweed_spread.gif', fps=4):
        """
        Create an animation of the seaweed spread over time.
        """
        try:
            import imageio.v2 as imageio
        except ImportError:
            print("Please install imageio with 'pip install imageio' to create animations")
            return
        
        import tempfile
        import os
        
        temp_dir = tempfile.mkdtemp()
        frames = []
        
        for i, grid in enumerate(self.history):
            fig, ax = plt.subplots(figsize=(10, 10))
            
            combined_map = np.zeros(self.grid_size, dtype=int)
            combined_map[self.land_grid] = 1
            combined_map[~self.land_grid & (grid == 1)] = 2 
            
            cmap = ListedColormap(['lightblue', 'green', 'red'])
            ax.imshow(combined_map, cmap=cmap)
            
            steps_per_year = 12
            year = i // steps_per_year
            month = i % steps_per_year
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            
            ax.set_title(f'Year {year+1}, {month_names[month]}')
            
            # Save the frame
            frame_path = os.path.join(temp_dir, f'frame_{i:04d}.png')
            plt.savefig(frame_path)
            frames.append(frame_path)
            plt.close()
        
        # Create the animation
        with imageio.get_writer(filename, mode='I', fps=fps, loop=0) as writer:
            for frame_path in frames:
                image = imageio.imread(frame_path)
                writer.append_data(image)

            pause_frames = int(fps * 2)
            final_image = imageio.imread(frames[-1])
            for _ in range(pause_frames):
                writer.append_data(final_image)
            for frame_path in frames:
                os.remove(frame_path)
        
        print(f"Animation saved as {filename}")

def main():
    # Initialize the model
    model = InvasiveSeaweedModel(grid_size=(100, 100), 
                                depth_threshold=40)
    
    # Set up the environment
    import TIFF_toGrid # Convert GEBCO GeoTIFF Grid to one compatible with model
    model.initialize_environment(TIFF_toGrid.depth_grid()==0, depth_map=TIFF_toGrid.depth_grid(), initial_seaweed=[(25,54)])
    
    print("Initial state:")
    model.visualize(show_depth=True, show_temp=True)
    
    print("Running simulation...")
    model.simulate(num_years=100)
    
    print("Final state after 100 years:")
    model.visualize(show_depth=True, show_temp=True)
    
    print("Creating animation...")
    model.create_animation(filename="seaweed"+str(np.random.rand())+".gif")

if __name__ == "__main__":
    main()